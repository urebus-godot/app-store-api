from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship
from sqlalchemy.dialects.postgresql import TIMESTAMP

from app.base_models.discussion import BaseDiscussion, BaseMessage


class DiscussionDB(BaseDiscussion, table=True):
    __tablename__ = "discussions"

    id: UUID = Field(primary_key=True, default_factory=uuid4)
    created_at: datetime = Field(
        sa_type=TIMESTAMP(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc)
        )
    messages: list["MessageDB"] = Relationship(
        back_populates="discussion",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    creator_id: UUID = Field(foreign_key="users.id")
    creator: "UserDB" = Relationship(back_populates="discussions")
    app_id: UUID = Field(foreign_key="apps.id")



class MessageDB(BaseMessage, table=True):
    __tablename__ = "messages"

    id: UUID = Field(primary_key=True, default_factory=uuid4)
    created_at: datetime = Field(
        sa_type=TIMESTAMP(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc)
        )

    author_id: UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    author: "UserDB" = Relationship(back_populates="messages")

    discussion_id: UUID = Field(
        foreign_key="discussions.id", ondelete="CASCADE"
    )
    discussion: "DiscussionDB" = Relationship(back_populates="messages")
