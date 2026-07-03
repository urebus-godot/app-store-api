from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship, Column, DateTime, func

# ----- Message Models -----

class BaseMessage(SQLModel):
    text: str = Field(le=400)


class MessageDB(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4)
    text: str = Field(le=400)

    author_id: UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    author: "UserDB" = Relationship(back_populates="messages")

    discussion_id: UUID = Field(
        foreign_key="discussion.id", ondelete="CASCADE"
        )
    discussion: DiscussionDB = Relationship("messages")


class MessageRequest(BaseMessage):
    pass


class MessageResponse(BaseMessage):
    id: UUID
    author: "UserBaseResponse"


# ----- Discussion Models -----

class DiscussionRequest(SQLModel):
    app_id: UUID
    topic: Optional[str]


class DiscussionDB(SQLModel, table=True):
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False
        )
    )
    messages: list[MessageDB] = Relationship(
        back_populates="discussion"
        )
    creator_id: UUID = Field(foreign_key="user.id")
    app_id: UUID = Field(foreign_key="app.id") 


class DiscussionResponse(SQLModel):
    created_at: datetime
    messages: list[MessageResponse] = []