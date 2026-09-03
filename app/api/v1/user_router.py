from typing import Annotated
from uuid import UUID
import logging

from fastapi import (
    APIRouter,
    Depends,
    status,
    Response,
    Request,
    BackgroundTasks
)
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import (
    UserDep,
    UserIdDep,
    SkipLimitParams,
    UserServiceDep,
    SendEmailDep,
    RefreshSecretKeyDep,
    AccessSecretKeyDep,
    rate_limit,
    RedisDep,
    check_admin_password,
    require_role
)
from app.core import auth
from app.utils.time import get_refresh_token_expire

from app.schemas.user import (
    UserRequest,
    UserResponse,
    UserUpdate,
    CurrentUserResponse,
    UserRole,
    UserRoleRequest,
    UserRoleResponse
)
from app.schemas.token import TokenResponse, LoginResponse

router = APIRouter(
    dependencies=[Depends(rate_limit)]
)

logger = logging.getLogger("api.v1.user_router")


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    response_model=CurrentUserResponse
)
async def register_user(
    data: UserRequest, 
    user_service: UserServiceDep
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
    sends_email: SendEmailDep,
    access_secret_key: AccessSecretKeyDep,
    refresh_secret_key: RefreshSecretKeyDep,
) -> LoginResponse:
    """Returns refresh and access tokens to the user on success."""
    login_response = await user_service.login(
        form_data.username,
        form_data.password,
        bg_tasks=bg_tasks,
        request=request,
        redis=redis,
        sends_email=sends_email,
        access_secret_key=access_secret_key,
        refresh_secret_key=refresh_secret_key
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
    secret_key: RefreshSecretKeyDep,
    user_service: UserServiceDep,
    redis: RedisDep,
) -> dict[str, str]:
    """Adds user's refresh token to the blacklist or deletes it from Redis."""
    refresh_token = request.cookies.pop("refresh_token", None)
    return await user_service.logout(refresh_token, redis, secret_key)


@router.post("/users/refresh")
async def refresh_tokens(
    request: Request,
    access_secret_key: AccessSecretKeyDep,
    refresh_secret_key: RefreshSecretKeyDep,
    redis: RedisDep,
    user_service: UserServiceDep
) -> TokenResponse:
    """Creates refresh and access tokens on success."""
    refresh_token = request.cookies.get("refresh_token")
    logger.info(f"Start refreshing token: \n{refresh_token=}")
    tokens = await auth.refresh_tokens(
        refresh_token=refresh_token, 
        redis=redis, 
        access_secret_key=access_secret_key,
        refresh_secret_key=refresh_secret_key,
        user_service=user_service
    )
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
    )


@router.post("/users/me/roles/publisher")
async def set_publisher_role(
    user_id: UserIdDep,
    user_service: UserServiceDep,
    secret_key: AccessSecretKeyDep
) -> UserRoleResponse:
    return await user_service.set_role(
        user_id, UserRole.PUBLISHER, secret_key
    )


@router.post(
    "/users/me/roles/admin",
    dependencies=[Depends(check_admin_password)]
)
async def set_admin_role(
    user_id: UserIdDep,
    user_service: UserServiceDep,
    secret_key: AccessSecretKeyDep
) -> UserRoleResponse:
    return await user_service.set_role(
        user_id, UserRole.ADMIN, secret_key
    )


@router.post(
    "/users/{user_id}/roles",
    dependencies=[Depends(require_role(UserRole.ADMIN))]
)
async def set_role_to_user(
    user_id: UUID,
    data: UserRoleRequest,
    user_service: UserServiceDep,
    secret_key: AccessSecretKeyDep
) -> UserRoleResponse:
    return await user_service.set_role(user_id, data.role, secret_key)


@router.patch("/users/me")
async def update_current_user(
    data: UserUpdate,
    user: UserDep,
    user_service: UserServiceDep
) -> CurrentUserResponse:
    """Changes attributes of user to the new ones"""
    return await user_service.update_user(user=user, data=data)


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
    bg_tasks: BackgroundTasks
) -> None:
    """Deletes user."""
    await user_service.delete_user(
        user_id=user_id, redis=redis, bg_tasks=bg_tasks
    )
