from datetime import datetime, date, timezone, timedelta
from uuid import UUID
from decimal import Decimal
from typing import Optional

from pydantic import EmailStr, ConfigDict, field_validator
from sqlmodel import SQLModel, Field

from app.base_models.user import BaseUser, UserRole
from app.core.config import settings


class UserRequest(BaseUser):
    password: str = Field(min_length=settings.MIN_PASSWORD_LEN)
    birth_date: Optional[date] = None

    @classmethod
    @field_validator("password")
    def validate_password(cls, value: str) -> str:
        if " " in value:
            raise ValueError("Password can't contain spaces")
        return value

    @classmethod
    @field_validator("username")
    def validate_username(cls, value: str) -> str:
        if " " in value:
            raise ValueError("Username can't contain spaces")
        return value

    @classmethod
    @field_validator("birth_date")
    def validate_birth_date(cls, value: date) -> date:
        current_date = datetime.now(timezone.utc).date()
        thirteen_years_ago = current_date.replace(year=current_date.year - 13)
        #thirteen_years_ago = current_date.replace(year=current_date.year - 13, day=28)
        if value > thirteen_years_ago:
            raise ValueError("You must be at least 13 to sign up")
        return value


class UserResponse(BaseUser):
    id: UUID
    registered_at: datetime

    roles: set[UserRole]

    model_config = ConfigDict(from_attributes=True)


class PublisherResponse(BaseUser):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class CurrentUserResponse(UserResponse):
    balance: Decimal
    birth_date: date


class UserResponseWithReviewsAndApps(UserResponse):
    reviews: list["ReviewResponse"]
    cart: list["AppResponse"]
    purchased_apps: list["AppResponse"]
    published_apps: list["AppResponse"]


class UserBaseResponse(BaseUser):
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(SQLModel):
    username: Optional[str] = Field(
        default=None, 
        min_length=settings.MIN_NAME_LEN
        )
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(
        default=None,
        min_length=settings.MIN_PASSWORD_LEN
        )
    
    @field_validator("password")
    def validate_password(cls, value: str) -> str:
        if " " in value:
            raise ValueError("Password can't contain spaces")
        return value

    @field_validator("username")
    def validate_username(cls, value: str) -> str:
        if " " in value:
            raise ValueError("Username can't contain spaces")
        return value