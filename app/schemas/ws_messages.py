from typing import Literal, Annotated, Union

from sqlmodel import SQLModel, Field
from pydantic import TypeAdapter


class AuthMessage(SQLModel):
    type: Literal["auth"] = "auth"
    token: str


class SendMessage(SQLModel):
    type: Literal["send_message"] = "send_message"
    text: str


class TypingMessage(SQLModel):
    type: Literal["user_typing"] = "user_typing"


IncomingMessage = Annotated[
    Union[AuthMessage, SendMessage, TypingMessage],
    Field(discriminator="type")
]
incoming_adapter: TypeAdapter[IncomingMessage] = TypeAdapter(IncomingMessage)