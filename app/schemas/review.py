from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import Field

from app.base_models.review import BaseReview


class ReviewRequest(BaseReview):
    pass


class ReviewUpdate(BaseReview):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    subject: Optional[str] = Field(default=None)
    content: Optional[str] = Field(default=None)


class ReviewResponse(BaseReview):
    id: UUID
    created_at: datetime
    author_id: UUID
    app_id: UUID
    model_config = ConfigDict(from_attributes=True)


class ReviewResponseWithAuthor(ReviewResponse):
    author: "UserResponse"
