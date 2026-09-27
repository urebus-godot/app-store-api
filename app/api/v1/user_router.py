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

from app.core.config import settings

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
from app.utils.time import days_to_seconds

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
    """Создаёт пользователя в базе данных.
    
    **Возвращает**: CurrentUserResponse"""
    return await user_service.register_user(data)


@router.post("/auth/login", tags=["Auth"])
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
    """Выполняет вход пользователя в систему: 
    аутентифицирует его, создаёт JWT refresh/access токены,
    устанавливает *refresh_token* куки.
    
    **Возвращает**: LoginResponse с refresh/access токенами."""
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
        samesite="lax",
        max_age=days_to_seconds(settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    return login_response


@router.post(
    "/auth/logout", 
    tags=["Auth"],
    status_code=status.HTTP_204_NO_CONTENT
)
async def logout(
    request: Request,
    response: Response,
    secret_key: RefreshSecretKeyDep,
    user_service: UserServiceDep,
    redis: RedisDep,
) -> None:
    """Отзывает refresh токен пользователя, 
    добавляет в чёрный список Redis и удаляет *refresh_token* куки.
    
    **Возвращает**: None."""
    refresh_token = request.cookies.get("refresh_token", None)
    await user_service.logout(refresh_token, redis, secret_key)
    response.delete_cookie(
        key="refresh_token", httponly=True, secure=True, samesite="lax"
    )


@router.post(
    "/auth/refresh", 
    tags=["Auth"]
)
async def refresh_tokens(
    request: Request,
    response: Response,
    access_secret_key: AccessSecretKeyDep,
    refresh_secret_key: RefreshSecretKeyDep,
    redis: RedisDep,
    user_service: UserServiceDep
) -> TokenResponse:
    """Создаёт новую пару JWT refresh/access токенов,
    старый refresh токен отправляется в чёрный список Redis.
    
    **Возвращает**: TokenResponse."""
    refresh_token = request.cookies.get("refresh_token")
    tokens = await user_service.refresh_tokens(
        refresh_token=refresh_token, 
        redis=redis, 
        access_secret_key=access_secret_key,
        refresh_secret_key=refresh_secret_key,
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=days_to_seconds(settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
    )


@router.post("/users/me/roles/publisher", tags=["Roles"])
async def set_publisher_role(
    user_id: UserIdDep,
    user_service: UserServiceDep,
    secret_key: AccessSecretKeyDep
) -> UserRoleResponse:
    """Назначает пользователю роль "*издатель*" ("*publisher*").
    
    **Возвращает**: UserRoleResponse."""
    return await user_service.set_role(
        user_id, UserRole.PUBLISHER, secret_key
    )


@router.post(
    "/users/me/roles/admin",
    dependencies=[Depends(check_admin_password)],
    tags=["Roles"]
)
async def set_admin_role(
    user_id: UserIdDep,
    user_service: UserServiceDep,
    secret_key: AccessSecretKeyDep
) -> UserRoleResponse:
    """Назначает пользователю роль "*администратор*" ("*admin*")
    при совпадении введённого пароля.
    
    **Возвращает**: UserRoleResponse."""
    return await user_service.set_role(
        user_id, UserRole.ADMIN, secret_key
    )


@router.post(
    "/users/{user_id}/roles",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
    tags=["Roles"]
)
async def set_role_to_user(
    user_id: UUID,
    data: UserRoleRequest,
    user_service: UserServiceDep,
    secret_key: AccessSecretKeyDep
) -> UserRoleResponse:
    """Назначает пользователю с указанным *id* указанную роль.

    **Возвращает**: UserRoleResponse."""
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
    """Обновляет атрибуты пользователя в базе данных.
    
    **Возвращает**: CurrentUserResponse."""
    return await user_service.update_user(user=user, data=data)


@router.get(
    "/users/me", 
    tags=["Users"],
    response_model=CurrentUserResponse
)
async def get_current_user(
    user: UserDep
) -> CurrentUserResponse:
    """Возвращает текущего пользователя.
    
    **Возвращает**: CurrentUserResponse."""
    return user


@router.get(
    "/users/{username}", 
    response_model=UserResponse,
    tags=["Users"]
)
async def get_user(
    username: str, user_service: UserServiceDep
) -> UserResponse:
    """Находит пользователя с указанным *id*.
    
    **Возвращает**: UserResponse."""
    return await user_service.get_user_by_username(username)


@router.get(
    "/users", 
    tags=["Users"],
    response_model=list[UserResponse]
)
async def get_users(
    skip_limit: SkipLimitParams, user_service: UserServiceDep
) -> list[UserResponse]:
    """Находит пользователей в базе данных.
    
    **Возвращает**: list[UserResponse]."""
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
    response: Response
) -> None:
    """Находит пользователей в базе данных.
    
    **Возвращает**: None."""
    await user_service.delete_user(
        user_id=user_id, redis=redis
    )
    response.delete_cookie(
        key="refresh_token", httponly=True, secure=True, samesite="lax"
    )