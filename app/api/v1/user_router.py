from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import (
    UserDep, SkipLimitParams,
    UserServiceDep, TokenDep
    )
from app.core import auth
from app.models.user import (
    UserRequest, UserResponse, UserUpdate, CurrentUserResponse)
from app.models.token import (
    RefreshTokenRequest, TokenResponse, LoginResponse)
from app.core.logging import logger

router = APIRouter()


@router.post("/users/register-user", status_code=status.HTTP_201_CREATED)
async def register_user(
    data: UserRequest,
    user_service: UserServiceDep
) -> UserResponse:
    logger.info("Start registering user!")
    return await user_service.register_user(data)


@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserServiceDep
) -> LoginResponse:
    logger.info("Start login")
    return await user_service.login(
        form_data.username, form_data.password
        )


@router.post("/users/logout")
async def logout(
    credentials: TokenDep,
    user_service: UserServiceDep,
    refresh_request: RefreshTokenRequest = None,
) -> dict[str, str]:
    return await user_service.logout(refresh_request, credentials)


@router.post("/users/refresh-token")
async def refresh_token(
    request: RefreshTokenRequest,
    user_service: UserServiceDep
) -> TokenResponse:
    username = auth.validate_refresh_token(request.refresh_token)
    new_access_token = auth.create_access_token(username)

    return TokenResponse(access_token=new_access_token)


@router.patch("/users/{username}")
async def update_current_user(
    data: UserUpdate,
    user: UserDep,
    user_service: UserServiceDep
) -> UserResponse:
    return await user_service.update_user(
        data=data, user=user
        )


@router.patch("/users/me/become-publisher")
async def become_publisher(
    user: UserDep,
    user_service: UserServiceDep
) -> dict[str, str]:
    return await user_service.become_publisher(user)


@router.post("/users/me/top-up-balance")
async def top_up_balance(
    amount: Decimal,
    user: UserDep,
    user_service: UserServiceDep
) -> dict[str, str]:
    return await user_service.top_up_balance(
        amount, user=user
        )


@router.get("/users/me")
async def get_current_user(
    user: UserDep
) -> CurrentUserResponse:
    return user


@router.get("/users/{username}")
async def get_user(
    username: str,
    user_service: UserServiceDep
) -> UserResponse:
    return await user_service.get_user(username=username)


@router.get("/users")
async def get_users(
    skip_limit: SkipLimitParams,
    user_service: UserServiceDep
) -> list[UserResponse]:
    skip, limit = skip_limit
    return await user_service.get_users(skip, limit)


@router.delete("/users/me")
async def delete_current_user(
    user: UserDep,
    user_service: UserServiceDep
) -> dict[str, str]:
    return await user_service.delete_user(user)