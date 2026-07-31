from uuid import UUID
from typing import Optional

from sqlmodel import SQLModel


class RefreshTokenRequest(SQLModel):
    refresh_token: str


class TokenResponse(SQLModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class LoginResponse(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: UUID
