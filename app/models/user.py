from datetime import date, UTC, datetime
from uuid import UUID, uuid4
from enum import StrEnum
from decimal import Decimal

from pydantic import EmailStr, ConfigDict
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String

from app.core.config import settings

class UserRole(StrEnum):
    USER = "user"
    PUBLISHER = "publisher"
    MODERATOR = "moderator"


class BaseUser(SQLModel):
    username: str = Field(
        index=True,
        min_length=settings.MIN_NAME_LEN,
        max_length=settings.MAX_NAME_LEN
        )
    email: EmailStr | None = None


class UserDB(BaseUser, table=True):
    __tablename__ = "user"

    id: UUID = Field(
        default_factory=lambda: uuid4(),
        primary_key=True
        )

    hashed_password: str
    roles: list["UserRole"] = Field(
        sa_type=ARRAY(String),
        default=[UserRole.USER]
        )

    registration_date: date = Field(
        default=datetime.now(UTC)
    )
    balance: Decimal = Field(default=0, ge=0)

    apps_to_purchase: list["AppDB"] = Relationship(
        back_populates="users_want_to_purchase"
        )
    purchased_apps: list["AppDB"] = Relationship(
        back_populates="users_purchased"
        )
    published_apps: list["AppDB"] = Relationship(
        back_populates="publisher"
        )

    reviews: list["ReviewDB"] = Relationship(
        back_populates="author"
        )



class UserRequest(BaseUser):
    password: str


class UserResponse(BaseUser):
    id: UUID
    registration_date: date

    roles: list[UserRole]
    model_config = ConfigDict(from_attributes=True)


class UserResponseWithReviewsAndApps(UserResponse):
    reviews: list["ReviewResponse"]
    apps_to_purchase: list["AppResponse"]
    purchased_apps: list["AppResponse"]
    published_apps: list["AppResponse"]


class UserUpdate(BaseUser):
    email: EmailStr | None = None
    password: str | None = None
    