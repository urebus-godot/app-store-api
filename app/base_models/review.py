
from sqlmodel import SQLModel, Field


class BaseReview(SQLModel):
    rating: int = Field(ge=1, le=5)
    subject: str | None = Field(default=None)
    content: str | None = Field(default=None)