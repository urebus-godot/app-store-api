from datetime import datetime
from uuid import UUID, uuid4
from enum import StrEnum
from decimal import Decimal
from typing import Optional

from pydantic import EmailStr, ConfigDict
from sqlmodel import SQLModel, Field, Relationship, Column, DateTime, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String

from app.models.app_purchase import Purchase
from app.core.config import settings

class UserRole(StrEnum):
    USER = "user"
    PUBLISHER = "publisher"
    MODERATOR = "moderator"


class BaseUser(SQLModel):
    username: str = Field(
        index=True,
        min_length=settings.MIN_NAME_LEN,
        max_length=settings.MAX_NAME_LEN,
        unique=True
        )
    email: Optional[EmailStr] = Field(default=None, unique=True)


class UserDB(BaseUser, table=True):
    __tablename__ = "users"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True
        )

    hashed_password: str
    roles: list["UserRole"] = Field(
        sa_type=ARRAY(String),
        default={UserRole.USER}
        )

    registered_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False
        )
    )
    balance: Decimal = Field(default=0, ge=0)

    cart: Optional["Cart"] = Relationship(
        back_populates="user", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
        )
    
    purchased_apps: list["AppDB"] = Relationship(
        back_populates="users_purchased", link_model=Purchase
        )
    published_apps: list["AppDB"] = Relationship(
        back_populates="publisher",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
        )

    reviews: list["ReviewDB"] = Relationship(
        back_populates="author",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
        )

    messages: list["MessageDB"] = Relationship(
        back_populates="author",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
        )


class UserRequest(BaseUser):
    password: str


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


class UserResponseWithReviewsAndApps(UserResponse):
    reviews: list["ReviewResponse"]
    cart: list["AppResponse"]
    purchased_apps: list["AppResponse"]
    published_apps: list["AppResponse"]


class UserBaseResponse(BaseUser):
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(SQLModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
