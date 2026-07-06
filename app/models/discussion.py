from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship, Column, DateTime, func
from pydantic import ConfigDict


# ----- Discussion Models -----

class BaseDiscussion(SQLModel):
    topic: Optional[str] = Field(default=None, max_length=80)


class DiscussionRequest(BaseDiscussion):
    pass


class DiscussionDB(BaseDiscussion, table=True):
    __tablename__ = "discussions"

    id: UUID = Field(primary_key=True, default_factory=uuid4)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False
        )
    )
    messages: list[MessageDB] = Relationship(
        back_populates="discussion", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
        )
    creator_id: UUID = Field(foreign_key="users.id")
    app_id: UUID = Field(foreign_key="apps.id")


class DiscussionResponse(BaseDiscussion):
    id: UUID
    created_at: datetime
    messages: list[MessageResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ShortDiscussionResponse(BaseDiscussion):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----- Message Models -----

class BaseMessage(SQLModel):
    text: str = Field(max_length=500)


class MessageDB(BaseMessage, table=True):
    __tablename__ = "messages"

    id: UUID = Field(primary_key=True, default_factory=uuid4)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False
        )
    )

    author_id: UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    author: "UserDB" = Relationship(back_populates="messages")

    discussion_id: UUID = Field(
        foreign_key="discussions.id", ondelete="CASCADE"
        )
    discussion: DiscussionDB = Relationship(back_populates="messages")


class MessageRequest(BaseMessage):
    pass


class MessageResponse(BaseMessage):
    id: UUID
    author: "UserBaseResponse"

    model_config = ConfigDict(from_attributes=True)
