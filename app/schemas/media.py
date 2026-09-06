from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class MediaConfirmResponse(BaseModel):
    url: str


class ConfirmCoverRequest(BaseModel):
    object_key: str


class AppCoverResponse(BaseModel):
    id: UUID
    url: str
    created_at: datetime


class AppCoverListResponse(BaseModel):
    covers: list[AppCoverResponse]
