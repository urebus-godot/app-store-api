from typing import Optional
from datetime import datetime, timezone

from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMP
from sqlalchemy import String, Index
from sqlmodel import Field, Relationship

from app.models.purchase import PurchaseDB
from app.base_models.app import BaseApp, GameGenre, AppCategory


class AppDB(BaseApp, table=True):
    __tablename__ = "apps"

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

    rating: Optional[float] = Field(
        default=None, 
        ge=1.0, le=5.0
        )
    times_purchased: int = Field(default=0, ge=0)
    #public: bool

    publisher_id: UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    publisher: "UserDB" = Relationship(back_populates="published_apps")
    
    users_purchased: list["UserDB"] = Relationship(
        back_populates="purchased_apps", link_model=PurchaseDB
    )

    pending_archive_key: Optional[str] = None
    archive_key: Optional[str] = None

    pending_icon_key: Optional[str] = None
    icon_key: Optional[str] = None

    reviews: list["ReviewDB"] = Relationship(
        back_populates="app",
        cascade_delete=True,
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    __table_args__ = (
        Index(
            "ix_apps_keywords_gin",
            "keywords",
            postgresql_using="gin",
            postgresql_where=("public")
        ),
    )
