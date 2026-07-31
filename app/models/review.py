from uuid import UUID, uuid4
from datetime import datetime, timezone

from sqlmodel import Field, Relationship
from sqlalchemy.dialects.postgresql import TIMESTAMP

from app.base_models.review import BaseReview


class ReviewDB(BaseReview, table=True):
    __tablename__ = "reviews"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    created_at: datetime = Field(
        sa_type=TIMESTAMP(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc)
        )

    author_id: UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    author: "UserDB" = Relationship(back_populates="reviews")

    app_id: UUID = Field(foreign_key="apps.id", ondelete="CASCADE")
    app: "AppDB" = Relationship(back_populates="reviews")

