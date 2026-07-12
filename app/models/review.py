from uuid import UUID, uuid4
from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import SQLModel, Field, Relationship


class BaseReview(SQLModel):
    rating: int = Field(ge=0, le=5)
    subject: str | None = Field(default=None, max_length=50)
    content: str | None = Field(default=None, max_length=400)


class ReviewDB(BaseReview, table=True):
    __tablename__ = "reviews"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now())

    author_id: UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    author: "UserDB" = Relationship(back_populates="reviews")

    app_id: UUID = Field(foreign_key="apps.id", ondelete="CASCADE")
    app: "AppDB" = Relationship(back_populates="reviews")


class ReviewRequest(BaseReview):
    pass


class ReviewResponse(BaseReview):
    id: UUID
    created_at: datetime
    author_id: UUID
    app_id: UUID
    model_config = ConfigDict(from_attributes=True)


class ReviewResponseWithAuthor(ReviewResponse):
    author: "UserResponse"
