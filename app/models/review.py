from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field

class BaseReview(SQLModel):
    rating: int = Field(ge=1, le=5)
    subject: str
    content: str


class ReviewDB(BaseReview):
    id: UUID = Field(default_factory=lambda: uuid4())


class ReviewRequest(BaseReview):
    pass


class ReviewResponse(BaseReview):
    id: UUID