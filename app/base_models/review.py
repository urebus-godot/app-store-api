from typing import Optional

from sqlmodel import SQLModel, Field


class BaseReview(SQLModel):
    rating: int = Field(ge=1, le=5)
    subject: Optional[str] = Field(default=None)
    content: Optional[str] = Field(default=None)