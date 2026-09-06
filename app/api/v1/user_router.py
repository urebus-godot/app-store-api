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
    response_model=CurrentUserResponse,
    tags=["Users"]
)
async def register_user(
    data: UserRequest, 
    user_service: UserServiceDep
) -> CurrentUserResponse:
    """Creates new user and adds it to the database.
    
    *Returns*: CurrentUserResponse object"""
    return await user_service.register_user(data)


@router.post("/users/login", tags=["Auth"])
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
    """Authenticates user and creates a pair of JWT access and refresh tokens.
    Then sets refresh token cookie.
    
    *Returns*: LoginResponse object"""
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


@router.post(
    "/users/logout", 
    tags=["Auth"],
    status_code=status.HTTP_204_NO_CONTENT
)
async def logout(
    request: Request,
    secret_key: RefreshSecretKeyDep,
    user_service: UserServiceDep,
    redis: RedisDep,
) -> None:
    """Adds the user's refresh token to the blacklist 
    and deletes it from Redis.
    
    *Returns*: None"""
    refresh_token = request.cookies.pop("refresh_token", None)
    await user_service.logout(refresh_token, redis, secret_key)


@router.post(
    "/users/refresh", 
    tags=["Auth"]
)
async def refresh_tokens(
    request: Request,
    access_secret_key: AccessSecretKeyDep,
    refresh_secret_key: RefreshSecretKeyDep,
    redis: RedisDep,
    user_service: UserServiceDep
) -> TokenResponse:
    """Creates a new pair of JWT refresh and access tokens.
        
    *Returns*: TokenResponse object"""
    refresh_token = request.cookies.get("refresh_token")
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


@router.post("/users/me/roles/publisher", tags=["Users"])
async def set_publisher_role(
    user_id: UserIdDep,
    user_service: UserServiceDep,
    secret_key: AccessSecretKeyDep
) -> UserRoleResponse:
    """Adds *publisher* role to the current user's roles.
        
    *Returns*: UserRoleResponse object"""
    return await user_service.set_role(
        user_id, UserRole.PUBLISHER, secret_key
    )


@router.post(
    "/users/me/roles/admin",
    dependencies=[Depends(check_admin_password)],
    tags=["Users"]
)
async def set_admin_role(
    user_id: UserIdDep,
    user_service: UserServiceDep,
    secret_key: AccessSecretKeyDep
) -> UserRoleResponse:
    """Adds *admin* role to the current user's roles
    if the entered password is correct.
        
    *Returns*: UserRoleResponse object"""
    return await user_service.set_role(
        user_id, UserRole.ADMIN, secret_key
    )


@router.post(
    "/users/{user_id}/roles",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
    tags=["Users"]
)
async def set_role_to_user(
    user_id: UUID,
    data: UserRoleRequest,
    user_service: UserServiceDep,
    secret_key: AccessSecretKeyDep
) -> UserRoleResponse:
    """Adds the specified role to the user's with the specified ID roles
    if the user has the admin role.
        
    *Returns*: UserRoleResponse object"""
    return await user_service.set_role(user_id, data.role, secret_key)


@router.patch(
    "/users/me", 
    tags=["Users"],
    response_model=CurrentUserResponse
)
async def update_current_user(
    data: UserUpdate,
    user: UserDep,
    user_service: UserServiceDep
) -> CurrentUserResponse:
    """Updates current user's attributes.
        
    *Returns*: CurrentUserResponse object"""
    return await user_service.update_user(user=user, data=data)


@router.get(
    "/users/me", 
    tags=["Users"],
    response_model=CurrentUserResponse
)
async def get_current_user(
    user: UserDep
) -> CurrentUserResponse:
    """Fetches the user with ID found in JWT access token.
        
    *Returns*: CurrentUserResponse object"""
    return user


@router.get(
    "/users/{username}", 
    response_model=UserResponse,
    tags=["Users"]
)
async def get_user(
    username: str, user_service: UserServiceDep
) -> UserResponse:
    """Fetches the user with the specified username.
        
    *Returns*: UserResponse object"""
    return await user_service.get_user_by_username(username)


@router.get(
    "/users", 
    tags=["Users"],
    response_model=list[UserResponse]
)
async def get_users(
    skip_limit: SkipLimitParams, user_service: UserServiceDep
) -> list[UserResponse]:
    """Fetches the users from the database.
        
    *Returns*: list of UserResponse objects"""
    skip, limit = skip_limit
    return await user_service.get_users(skip, limit)


@router.delete(
    "/users/me", 
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Users"]
)
async def delete_current_user(
    user_id: UserIdDep,
    redis: RedisDep,
    user_service: UserServiceDep,
    bg_tasks: BackgroundTasks
) -> None:
    """Deletes the current user and his files.
        
    *Returns*: None"""
    await user_service.delete_user(
        user_id=user_id, redis=redis, bg_tasks=bg_tasks
    )
