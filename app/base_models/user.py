from enum import StrEnum
from typing import Optional

from sqlmodel import SQLModel, Field
from pydantic import EmailStr

from app.core.config import settings


class UserRole(StrEnum):
    USER = "user"
    PUBLISHER = "publisher"
    ADMIN = "admin"


class BaseUser(SQLModel):
    username: str = Field(
        index=True,
        min_length=settings.MIN_NAME_LEN,
        max_length=settings.MAX_NAME_LEN,
        unique=True,
    )
    email: Optional[EmailStr] = Field(default=None, unique=True)
