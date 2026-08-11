from uuid import UUID
from typing import Literal, Annotated, Union

from sqlmodel import SQLModel, Field
from pydantic import TypeAdapter

from app.schemas.discussion import MessageResponse


class AuthMessageEvent(SQLModel):
    type: Literal["auth"] = "auth"
    token: str


class SendMessage(SQLModel):
    type: Literal["send_message"] = "send_message"
    text: str


class TypingMessage(SQLModel):
    type: Literal["user_joined"] = "user_joined"
    text: str


IncomingMessage = Annotated[
    Union[AuthMessageEvent, SendMessage, TypingMessage],
    Field(discriminator="type")
]
incoming_adapter: TypeAdapter[IncomingMessage] = TypeAdapter(IncomingMessage)