from uuid import UUID
from typing import Literal, Annotated, Union

from sqlmodel import SQLModel, Field

from app.schemas.discussion import MessageResponse


class NewMessageEvent(SQLModel):
    type: Literal["new_message"] = "new_message"
    message: MessageResponse


class UserTypingEvent(SQLModel):
    type: Literal["user_typing"] = "user_typing"
    user_id: UUID
    discussion_id: UUID


class UserJoinedEvent(SQLModel):
    type: Literal["user_joined"] = "user_joined"
    user_id: UUID
    username: UUID


class ErrorEvent(SQLModel):
    type: Literal["error"] = "error"
    detail: str


OutgoingEvent = Annotated[
    Union[NewMessageEvent, UserTypingEvent, UserJoinedEvent, ErrorEvent],
    Field(discriminator="type")
]