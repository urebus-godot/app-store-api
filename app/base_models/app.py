from typing import Optional

from decimal import Decimal
from enum import StrEnum

from sqlmodel import SQLModel, Field
from pydantic import field_validator

from app.core.config import settings


class GameGenre(StrEnum):
    ADVENTURE = "adventure"
    ACTION = "action"
    PUZZLE = "puzzle"
    RACING = "racing"
    SANDBOX = "sandbox"
    MISC = "misc"


class AppCategory(StrEnum):
    APPLICATION = "application"
    GAME = "game"


class BaseApp(SQLModel):
    title: str = Field(
        min_length=settings.MIN_TITLE_LEN, max_length=settings.MAX_TITLE_LEN
    )
    description: Optional[str] = Field(
        default=None
    )
    price: Decimal = Field(default=0.0, ge=0.0)
    public: bool = True
    keywords: Optional[set[str]] = Field(default=None)
    version: str = Field(default="1.0")