from typing import Optional
from datetime import datetime, timezone

from uuid import UUID, uuid4
from decimal import Decimal
from enum import StrEnum

from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String
from sqlmodel import SQLModel, Field, Relationship, Column, DateTime, func
from pydantic import ConfigDict
from fastapi import UploadFile

from app.models.purchase import PurchaseDB
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


class AppFile(SQLModel):
    app_id: UUID
    file: UploadFile
    filename: str


class BaseApp(SQLModel):
    title: str = Field(
        min_length=settings.MIN_TITLE_LEN, max_length=settings.MAX_TITLE_LEN
    )
    description: Optional[str] = Field(
        default=None, max_length=settings.MAX_DESC_LEN
    )
    price: Decimal = Field(default=0.0, ge=0.0)
    public: bool = True
    keywords: Optional[set[str]] = Field(default=None)
    version: str = Field(default="1.0")


class AppDB(BaseApp, table=True):
    __tablename__ = "apps"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    published_at: datetime = Field(
        default_factory=lambda: datetime.now()
    )
    genre: Optional[GameGenre] = Field(default=None, nullable=True)
    category: AppCategory = AppCategory.APPLICATION
    file_id: UUID = Field(default_factory=uuid4)

    keywords: Optional[set[str]] = Field(
        default=None, sa_type=ARRAY(String)
        )

    publisher_id: UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    publisher: "UserDB" = Relationship(back_populates="published_apps")

    users_purchased: list["UserDB"] = Relationship(
        back_populates="purchased_apps", link_model=PurchaseDB
    )

    reviews: list["ReviewDB"] = Relationship(
        back_populates="app",
        cascade_delete=True,
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class AppRequest(BaseApp):
    pass
    # @model_validator(mode="before")
    # def validate_game_genre(self):
    #    if (self.category == AppCategory.APPLICATION
    #        and self.game_genre is not None):
    #        raise ValueError("Non-game application can't have a game genre")


class AppResponse(BaseApp):
    id: UUID
    category: AppCategory = AppCategory.APPLICATION
    published_at: datetime
    rating: Optional[float] = Field(default=None, gt=0.0, le=5.0)

    model_config = ConfigDict(from_attributes=True)


class AppResponseWithPublisher(AppResponse):
    publisher: "PublisherResponse"


class AppResponseWithReviews(AppResponse):
    id: UUID
    reviews: list["ReviewResponse"]


class AppUpdate(SQLModel):
    title: Optional[str] = Field(
        default=None,
        min_length=settings.MIN_TITLE_LEN,
        max_length=settings.MAX_TITLE_LEN,
    )
    description: Optional[str] = Field(
        default=None, max_length=settings.MAX_DESC_LEN
    )
    price: Optional[Decimal] = Field(default=0.0, ge=0.0)
    public: Optional[bool] = None
    keywords: Optional[set[str]] = Field(default=None)
    version: Optional[str] = Field(default="1.0")


class GameRequest(AppRequest):
    genre: GameGenre = GameGenre.MISC


class GameResponse(AppResponse):
    genre: GameGenre
    category: AppCategory = AppCategory.GAME


class GameResponseWithPublisher(GameResponse):
    publisher: "PublisherResponse"


def rebuild_models() -> None:
    AppResponse.model_rebuild()
    GameResponse.model_rebuild()


# rebuild_models()
