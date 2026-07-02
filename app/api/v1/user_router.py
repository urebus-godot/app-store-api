from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, status, Response
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
from app.dependencies import RedisDep

router = APIRouter()


@router.post("/users/register-user", status_code=status.HTTP_201_CREATED)
async def register_user(
    data: UserRequest,
    user_service: UserServiceDep
) -> CurrentUserResponse:
    return await user_service.register_user(data)


@router.post("/users/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserServiceDep,
    redis: RedisDep,
    response: Response
) -> LoginResponse:
    login_response = await user_service.login(
        form_data.username, form_data.password, redis
        )

    return login_response
    response.set_cookie(
        key="refresh-token", 
        value=login_response.refresh_token,
        httponly=True
        )

@router.post("/users/logout")
async def logout(
    refresh_token: str,
    user_service: UserServiceDep,
    redis: RedisDep
) -> dict[str, str]:
    return await user_service.logout(refresh_token, redis)


@router.post("/users/refresh")
async def refresh_tokens(
    refresh_token: str,
    redis: RedisDep,
) -> TokenResponse:
    logger.info(f"Start refreshing token: \n{refresh_token=}")
    tokens = await auth.refresh_tokens(refresh_token, redis)

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"]
        )


@router.post("/users/me/top-up-balance")
async def top_up_balance(
    amount: Decimal,
    user: UserDep,
    user_service: UserServiceDep
) -> dict[str, str]:
    return await user_service.top_up_balance(
        amount, user=user
        )


@router.post("/users/me/become-publisher")
async def become_publisher(
    user: UserDep,
    user_service: UserServiceDep
) -> dict[str, str]:
    return await user_service.become_publisher(user)


@router.patch("/users/me")
async def update_current_user(
    data: UserUpdate,
    user: UserDep,
    user_service: UserServiceDep
) -> UserResponse:
    return await user_service.update_user(
        data=data, user=user
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