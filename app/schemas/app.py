from typing import Optional
from datetime import datetime

from uuid import UUID
from decimal import Decimal

from sqlmodel import SQLModel, Field
from pydantic import (
    ConfigDict, field_validator, field_serializer
)
from app.base_models.app import BaseApp, GameGenre, AppCategory
from app.core.config import settings


class AppRequest(BaseApp):
    @field_validator("title", check_fields=False)
    @classmethod
    def validate_title(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Title can't consist only of spaces")
        return value


class AppResponse(BaseApp):
    id: UUID
    category: AppCategory = AppCategory.APPLICATION
    published_at: datetime
    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    times_purchased: int = Field(ge=0)

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("rating")
    def serialize_rating(self, value: Decimal) -> float:
        return round(float(value), 1)

    @field_serializer("price")
    def serialize_price(self, value: Decimal) -> float:
        return round(float(value), 2)


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
        default=None
    )
    price: Optional[Decimal] = Field(default=0.0, ge=0.0)
    public: Optional[bool] = None
    keywords: Optional[set[str]] = Field(default=None)
    version: Optional[str] = Field(default="1.0")

    @field_validator("title", check_fields=False)
    @classmethod
    def validate_title(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Title can't consist only of spaces")
        return value


class GameUpdate(AppUpdate):
    genre: GameGenre


class GameRequest(AppRequest):
    genre: GameGenre = GameGenre.MISC


class GameResponse(AppResponse):
    genre: GameGenre
    category: AppCategory = AppCategory.GAME


class GameResponseWithPublisher(GameResponse):
    publisher: "PublisherResponse"


#game_list_adapter = TypeAdapter(list[GameResponseWithPublisher])