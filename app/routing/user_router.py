from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestFormStrict

from app.core.dependencies import (
    SessionDep, UserDep, CredentialsDep, SkipLimitParams)
from app.core import auth
from app.models.user import UserRequest, UserResponse, UserUpdate
from app.models.token import (
    RefreshTokenRequest, TokenResponse, LoginResponse)
from app.service import user_service

router = APIRouter(prefix="/api/v1")


@router.post("/users/register-user")
async def register_user(
    data: UserRequest,
    session: SessionDep
) -> UserResponse:
    return await user_service.register_user(data, session)


@router.post("/users/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestFormStrict, Depends()],
    session: SessionDep
) -> LoginResponse:
    return await user_service.login(
        form_data.username, form_data.password, session
        )


@router.post("/users/logout")
async def logout(
    credentials: CredentialsDep,
    refresh_request: RefreshTokenRequest = None,
) -> dict[str, str]:
    return await user_service.logout(refresh_request, credentials)


@router.post("/users/refresh-token")
async def refresh_token(
    request: RefreshTokenRequest
) -> TokenResponse:
    username = auth.validate_refresh_token(request.refresh_token)
    new_access_token = auth.create_access_token(username)

    return TokenResponse(access_token=new_access_token)


@router.patch("/users/{username}")
async def update_current_user(
    data: UserUpdate,
    user: UserDep,
    session: SessionDep
) -> UserResponse:
    return await user_service.update_user(data, user, session)


@router.post("/users/me/top-up-balance")
async def top_up_balance(
    amount: Decimal,
    user: UserDep,
    session: SessionDep
) -> dict[str, str]:
    return await user_service.top_up_balance(
        amount, session, user=user
        )


@router.get("/users/me")
async def get_current_user(
    user: UserDep
) -> UserResponse:
    return user


@router.get("/users/{username}")
async def get_user(
    username: str,
    session: SessionDep
) -> UserResponse:
    return await user_service.get_user(session, username=username)


@router.get("/users")
async def get_users(
    skip_limit: SkipLimitParams,
    session: SessionDep
) -> list[UserResponse]:
    skip, limit = skip_limit
    return await user_service.get_users(session, skip, limit)


@router.delete("/users/me")
async def delete_current_user(
    user: UserDep,
    session: SessionDep
) -> dict[str, str]:
    return await user_service.delete_user(user, session)