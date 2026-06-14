from sqlmodel import SQLModel, Field

class BaseReview(SQLModel):
    rating: int = Field(ge=1, le=5)
    subject: str
    content: str


class ReviewDB(BaseReview):
    pass


class ReviewRequest(BaseReview):
    pass


class ReviewResponse(BaseReview):
    pass