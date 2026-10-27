from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal

from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMP
from sqlalchemy import String, Index, Numeric, CheckConstraint
from sqlmodel import Field, Relationship

from app.models.purchase import PurchaseDB
from app.base_models.app import BaseApp, GameGenre, AppCategory


class AppDB(BaseApp, table=True):
    __tablename__ = "apps"

    __table_args__ = (
        Index(
            "ix_apps_keywords_gin_public",
            "keywords",
            postgresql_using="gin",
            postgresql_where=("public = true")
        ),
        CheckConstraint(
            "rating >= 0 AND rating <= 5", name="rating_range"
        )
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    published_at: datetime = Field(
        sa_type=TIMESTAMP(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    genre: Optional[GameGenre] = Field(default=None, nullable=True)
    category: AppCategory = AppCategory.APPLICATION
    keywords: Optional[list[str]] = Field(
        default=None, sa_type=ARRAY(String)
    )
    rating: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(3, 2),
        nullable=False
    )
    reviews_count: int = Field(default=0, ge=0)
    times_purchased: int = Field(default=0, ge=0)

    pending_archive_key: Optional[str] = None
    archive_key: Optional[str] = None

    pending_icon_key: Optional[str] = None
    icon_key: Optional[str] = None

    publisher_id: UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    publisher: "UserDB" = Relationship(back_populates="published_apps")
    users_purchased: list["UserDB"] = Relationship(
        back_populates="purchased_apps", link_model=PurchaseDB
    )
    reviews: list["ReviewDB"] = Relationship(
        back_populates="app",
        cascade_delete=True,
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    covers: list["AppCoverDB"] = Relationship(
        back_populates="app",
        cascade_delete=True,
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
