from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
    Response,
    Request,
    BackgroundTasks,
    UploadFile
)
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import (
    UserDep,
    UserIdDep,
    SkipLimitParams,
    UserServiceDep,
    SendEmailDep,
    RefreshSecretKeyDep,
    rate_limit,
    UnitOfWorkDep,
    RedisDep
)
from app.core.logging import logger
from app.core import auth
from app.utils.time import get_refresh_token_expire

from app.schemas.user import (
    UserRequest,
    UserResponse,
    UserUpdate,
    CurrentUserResponse
)
from app.models.file import UserProfilePicture
from app.schemas.token import TokenResponse, LoginResponse


router = APIRouter(
    dependencies=[Depends(rate_limit)]
)


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    response_model=CurrentUserResponse
)
async def register_user(
    data: UserRequest, 
    user_service: UserServiceDep,
    uow: UnitOfWorkDep
) -> CurrentUserResponse:
    """Creates new user."""
    return await user_service.register_user(data, uow)


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
        expires=get_refresh_token_expire()
    )

    return login_response


@router.post("/users/logout")
async def logout(
    request: Request,
    user_id: UserIdDep,
    secret_key: RefreshSecretKeyDep,
    user_service: UserServiceDep,
    redis: RedisDep,
) -> dict[str, str]:
    """Adds user's refresh token to the blacklist or deletes it from Redis."""
    refresh_token = request.cookies.get("refresh_token")
    return await user_service.logout(refresh_token, redis, secret_key)


@router.post("/users/refresh")
async def refresh_tokens(
    request: Request,
    secret_key: RefreshSecretKeyDep,
    redis: RedisDep,
) -> TokenResponse:
    """Creates refresh and access tokens on success."""
    refresh_token = request.cookies.get("refresh_token")
    logger.info(f"Start refreshing token: \n{refresh_token=}")
    tokens = await auth.refresh_tokens(refresh_token, redis, secret_key)
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
    )


@router.post("/users/me/publisher")
async def become_publisher(
    user: UserDep, 
    user_service: UserServiceDep,
    uow: UnitOfWorkDep
) -> dict[str, str]:
    """Adds "publisher" role to user roles on success."""
    return await user_service.become_publisher(user, uow)


@router.post(
    "/users/me/profile_picture",
    status_code=status.HTTP_201_CREATED
    )
async def upload_profile_picture(
    request: Request,
    file: UploadFile,
    user: UserDep,
    uow: UnitOfWorkDep,
    user_service: UserServiceDep
) -> UserProfilePicture:
    request.headers
    result = await user_service.upload_profile_picture(
        request, file, user.id, uow
        )
    return result


@router.delete(
    "/users/me/profile_picture",
    status_code=status.HTTP_204_NO_CONTENT
    )
async def remove_profile_picture(
    user_id: UserIdDep,
    user_service: UserServiceDep,
    uow: UnitOfWorkDep
) -> None:
    await user_service.remove_profile_picture_by_user(user_id, uow)


@router.patch("/users/me")
async def update_current_user(
    data: UserUpdate,
    user: UserDep,
    user_service: UserServiceDep,
    uow: UnitOfWorkDep
) -> CurrentUserResponse:
    """Changes attributes of user to the new ones"""
    return await user_service.update_user(user=user, data=data, uow=uow)


@router.get("/users/me")
async def get_current_user(
    user: UserDep
    ) -> CurrentUserResponse:
    """Returns user that was found by JWT access token. 
    The balance is measured in rubles"""
    return user


@router.get(
    "/users/{username}", 
    response_model=UserResponse
    )
async def get_user(
    username: str, user_service: UserServiceDep
) -> UserResponse:
    """Returns user from the db with specified username."""
    return await user_service.get_user_by_username(username)


@router.get("/users")
async def get_users(
    skip_limit: SkipLimitParams, user_service: UserServiceDep
) -> list[UserResponse]:
    """Returns all users from db."""
    skip, limit = skip_limit
    return await user_service.get_users(skip, limit)


@router.delete(
    "/users/me", 
    status_code=status.HTTP_204_NO_CONTENT,
    )
async def delete_current_user(
    user_id: UserIdDep,
    redis: RedisDep,
    user_service: UserServiceDep,
    uow: UnitOfWorkDep
) -> None:
    """Deletes user."""
    await user_service.delete_user(user_id, redis, uow)
