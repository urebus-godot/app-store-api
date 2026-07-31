from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict

from app.base_models.discussion import BaseDiscussion, BaseMessage


# ----- Discussion Models -----

class DiscussionRequest(BaseDiscussion):
    pass


class DiscussionResponse(BaseDiscussion):
    id: UUID
    created_at: datetime
    messages: list["MessageResponse"] = []

    model_config = ConfigDict(from_attributes=True)


class ShortDiscussionResponse(BaseDiscussion):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----- Message Models -----

class MessageRequest(BaseMessage):
    pass


class MessageResponse(BaseMessage):
    id: UUID
    created_at: datetime
    author: "UserBaseResponse"

    model_config = ConfigDict(from_attributes=True)
