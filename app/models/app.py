from typing import Optional

from uuid import UUID, uuid4
from decimal import Decimal
from enum import StrEnum

from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String
from sqlmodel import SQLModel, Field, Relationship
from pydantic import model_validator
from fastapi import UploadFile

from app.core.config import settings

class GameGenre(StrEnum):
    ADVENTURE = "adventure"
    PUZZLE = "puzzle"
    RACING = "racing"
    SANDBOX = "sandbox"


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
    description: str | None = Field(
        default=None,
        max_length=settings.MAX_DESC_LEN
        )
    category: AppCategory = AppCategory.APPLICATION
    price: Decimal = Decimal(0)
    public: bool = True
    keywords: set[str] = Field(
        default=[title], min_items=1, max_items=20
        )


class AppDB(BaseApp, table=True):
    __tablename__ = "app"

    id: Optional[UUID] = Field(
        default_factory=lambda: uuid4(),
        primary_key=True
        )
    genre: Optional[GameGenre] = None
    file_id: UUID

    keywords: set[str] = Field(sa_type=ARRAY(String))

    publisher_id: UUID = Field(foreign_key="user.id")
    publisher: "UserDB" = Relationship(back_populates="published_apps")

    users_want_to_purchase: list["UserDB"] = Relationship(
        back_populates="apps_to_purchase"
    )

    users_purchased: list["UserDB"] = Relationship(
        back_populates="purchased_apps"
    )

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