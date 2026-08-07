from pydantic import BaseModel

import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class UploadPresignRequest(BaseModel):
    filename: str
    content_type: str


class UploadPresignResponse(BaseModel):
    upload_url: str
    object_key: str
    expires_in: int


class DownloadPresignResponse(BaseModel):
    download_url: str
    expires_in: int

