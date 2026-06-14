from datetime import date, UTC
from pydantic import EmailStr
from sqlmodel import SQLModel, Field

class BaseUser(SQLModel):
    username: str
    email: EmailStr | None = None


class UserDB(BaseUser):
    registration_date: date = Field(default=function.now(UTC))


class UserRequest(BaseUser):
    password: str


class UserResponse(BaseUser):
    pass