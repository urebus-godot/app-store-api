from datetime import date, UTC
from uuid import UUID, uuid4
from enum import StrEnum
from decimal import Decimal

from pydantic import EmailStr
from sqlmodel import SQLModel, Field

class UserRole(StrEnum):
    DEVELOPER = "developer"
    MODERATOR = "moderator"
    USER = "user"


class BaseUser(SQLModel):
    username: str
    email: EmailStr | None = None


class UserDB(BaseUser):
    id: UUID = Field(default_factory=lambda: uuid4())
    registration_date: date = Field(default=function.now(UTC))
    hashed_password: str
    role: UserRole = UserRole.USER
    balance: Decimal = Field(default=0, ge=0)


class UserRequest(BaseUser):
    password: str


class UserResponse(BaseUser):
    id: UUID


class UserUpdate(BaseUser):
    email: EmailStr | None = None
    