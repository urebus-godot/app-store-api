from uuid import UUID
from typing import Optional

from sqlmodel import SQLModel

from app.schemas.user import UserRole


class TokenResponse(SQLModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class LoginResponse(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: UUID


class TokenData(SQLModel):
    user_id: UUID
    roles: list[UserRole]