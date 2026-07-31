from uuid import UUID
from datetime import datetime

from pydantic import ConfigDict

from app.base_models.review import BaseReview


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
