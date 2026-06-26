from typing import Optional, Annotated
from datetime import date, UTC, datetime
import re

from uuid import UUID, uuid4
from decimal import Decimal
from enum import StrEnum

from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String
from sqlmodel import SQLModel, Field, Relationship, Column, DateTime, func
from pydantic import model_validator, ConfigDict, field_validator
from fastapi import UploadFile

from app.models.app_purchase import Purchase, CartItem
from app.core.config import settings

class GameGenre(StrEnum):
    ADVENTURE = "adventure"
    PUZZLE = "puzzle"
    RACING = "racing"
    SANDBOX = "sandbox"
    MISC = "misc"
    NONE = "none"


class AppCategory(StrEnum):
    APPLICATION = "application"
    GAME = "game"


class AppFile(SQLModel):
    app_id: UUID
    file: UploadFile
    filename: str


class BaseApp(SQLModel):
    title: str = Field(
        min_length=settings.MIN_TITLE_LEN,
        max_length=settings.MAX_TITLE_LEN
        )
    description: Optional[str] = Field(
        default=None,
        max_length=settings.MAX_DESC_LEN
        )
    price: Decimal = Field(default=0.0, ge=0.0)
    public: bool = True
    keywords: Optional[set[str]] = Field(
        default=None
        )
    version: str = Field(default="1.0")

    #@field_validator("version", mode="before")
    #def validate_version(cls, value) -> str:
    #    re


class AppDB(BaseApp, table=True):
    __tablename__ = "app"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True
        )
    
    published_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False
        )
    )
    genre: Optional[GameGenre] = Field(default=GameGenre.NONE, nullable=True)
    category: AppCategory = AppCategory.APPLICATION
    file_id: UUID = Field(default_factory=uuid4)

    keywords: set[str] = Field(sa_type=ARRAY(String))

    publisher_id: UUID = Field(foreign_key="user.id")
    publisher: "UserDB" = Relationship(back_populates="published_apps")

    users_purchased: list["UserDB"] = Relationship(
        back_populates="purchased_apps", link_model=Purchase
    )
    #in_carts_of: list["UserDB"] = Relationship(
    #    back_populates="apps_cart", link_model=CartItem
    #)

    reviews: list["ReviewDB"] = Relationship(back_populates="app")


class AppRequest(BaseApp):
    pass
    #@model_validator(mode="before")
    #def validate_game_genre(self):
    #    if (self.category == AppCategory.APPLICATION 
    #        and self.game_genre is not None):
    #        raise ValueError("Non-game application can't have a game genre")


class AppResponse(BaseApp):
    id: UUID
    model_config = ConfigDict(from_attributes=True)
    category: AppCategory = AppCategory.APPLICATION
    published_at: datetime
    rating: Optional[float] = Field(default=None, gt=0.0, lt=5.0)
    #publisher: "UserResponse"


class AppResponseWithReviews(AppResponse):
    id: UUID
    reviews: list["ReviewResponse"]


class AppUpdate(BaseApp):
    pass


class GameRequest(AppRequest):
    genre: GameGenre


class GameResponse(AppResponse):
    genre: GameGenre
    category: AppCategory = AppCategory.GAME


def rebuild_models() -> None:
    AppResponse.model_rebuild()
    GameResponse.model_rebuild()


#rebuild_models()