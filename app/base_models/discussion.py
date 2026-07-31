from typing import Optional

from sqlmodel import SQLModel, Field


class BaseDiscussion(SQLModel):
    topic: Optional[str] = Field(default=None)



class BaseMessage(SQLModel):
    text: str
