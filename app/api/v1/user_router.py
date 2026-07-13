from decimal import Decimal
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
    Response,
    Request,
    BackgroundTasks,
)
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import (
    UserDep,
    UserIdDep,
    SkipLimitParams,
    UserServiceDep,
    UnitOfWorkDep,
    SendEmailDep
)
from app.core import auth
from app.utils.time import get_refresh_token_expire
from app.models.user import (
    UserRequest,
    UserResponse,
    UserUpdate,
    CurrentUserResponse,
)
from app.models.finance import TransferRequest
from app.models.token import TokenResponse, LoginResponse
from app.core.logging import logger
from app.dependencies import RedisDep

router = APIRouter()


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    response_model=CurrentUserResponse,
)
async def register_user(
    data: UserRequest, user_service: UserServiceDep
) -> CurrentUserResponse:
    """Creates new user."""
    return await user_service.register_user(data)


@router.post("/users/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserServiceDep,
    redis: RedisDep,
    request: Request,
    response: Response,
    bg_tasks: BackgroundTasks,
    sends_email: SendEmailDep
) -> LoginResponse:
    """Returns refresh and access tokens to the user on success."""

    login_response = await user_service.login(
        form_data.username,
        form_data.password,
        bg_tasks=bg_tasks,
        request=request,
        redis=redis,
        sends_email=sends_email
    )

    response.set_cookie(
        key="refresh_token",
        value=login_response.refresh_token,
        httponly=True,
        secure=True,
        expires=get_refresh_token_expire(),
    )

    return login_response


@router.post("/users/logout")
async def logout(
    # refresh_token: str,
    request: Request,
    user_id: UserIdDep,
    user_service: UserServiceDep,
    redis: RedisDep,
) -> dict[str, str]:
    """Adds user's refresh token to the blacklist or deletes it from Redis."""
    refresh_token = request.cookies.get("refresh_token")
    return await user_service.logout(refresh_token, redis)


@router.post("/users/refresh")
async def refresh_tokens(
    request: Request,
    # refresh_token: str,#Annotated[str, Body()],
    redis: RedisDep,
) -> TokenResponse:
    """Creates refresh and access tokens on success."""
    refresh_token = request.cookies.get("refresh_token")
    logger.info(f"Start refreshing token: \n{refresh_token=}")
    tokens = await auth.refresh_tokens(refresh_token, redis)
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
    )


@router.post("/users/me/publisher")
async def become_publisher(
    user: UserDep, user_service: UserServiceDep
) -> dict[str, str]:
    """Adds "publisher" role to user roles on success."""
    return await user_service.become_publisher(user)


@router.patch("/users/me")
async def update_current_user(
    data: UserUpdate,
    user: UserDep,
    user_service: UserServiceDep
) -> CurrentUserResponse:
    """Changes attributes of user to the new ones"""
    return await user_service.update_user(user=user, data=data)


@router.get("/users/me")
async def get_current_user(user: UserDep) -> CurrentUserResponse:
    """Returns user retrieved via *dependency injection*."""
    return user


@router.get("/users/{username}", response_model=UserResponse)
async def get_user(
    username: str, user_service: UserServiceDep
) -> UserResponse:
    """Returns user from the db with specified username."""
    return await user_service.get_user(username=username)


@router.get("/users")
async def get_users(
    skip_limit: SkipLimitParams, user_service: UserServiceDep
) -> list[UserResponse]:
    """Returns all users from db."""
    skip, limit = skip_limit
    return await user_service.get_users(skip, limit)


@router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    user: UserDep,
    redis: RedisDep,
    user_service: UserServiceDep
) -> None:
    """Deletes user."""
    await user_service.delete_user(user, redis)
