from uuid import UUID, uuid4
from typing import Optional
from datetime import date, datetime, UTC

from pydantic import ConfigDict
from sqlmodel import SQLModel, Field, Relationship

class BaseReview(SQLModel):
    rating: int = Field(ge=1, le=5)
    subject: str | None = Field(default=None, max_length=50)
    content: str | None = Field(default=None, max_length=400)


class ReviewDB(BaseReview, table=True):
    __tablename__ = "review"

    id: UUID = Field(
        default_factory=lambda: uuid4(),
        primary_key=True
        )
    creation_date: date = Field(default_factory=datetime.now(UTC))

    author_id: UUID = Field(foreign_key="user.id")
    author: "UserDB" = Relationship(back_populates="reviews")

    app_id: UUID = Field(foreign_key="app.id")
    app: "AppDB" = Relationship(back_populates="reviews")


class ReviewRequest(BaseReview):
    pass


class ReviewResponse(BaseReview):
    id: UUID
    creation_date: date
    author_username: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
    #author: "UserResponse"


class ReviewResponseWithAuthor(ReviewResponse):
    author: "UserResponse"