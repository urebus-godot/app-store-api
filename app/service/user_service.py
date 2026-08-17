from typing import Optional, Union
from uuid import UUID
import json

from fastapi import BackgroundTasks, Request
from pydantic import EmailStr
from jwt.exceptions import DecodeError
import jwt

from app.db.redis import Redis

from app.base_models.user import UserRole
from app.models.user import UserDB
from app.schemas.user import UserRequest, UserUpdate, UserRoleResponse
from app.schemas.token import LoginResponse

from app.repo.user_repo import UserRepository
from app.service.app_service import AppService

from app.core.exceptions import (
    user_not_found_exception,
    email_used_exception,
    username_used_exception,
    already_has_role_exception,
    incorrect_creds_exception,
    user_data_used_exception,
    invalid_refresh_token_exception
)
from app.core.security import verify_password, get_password_hash
from app.core.auth import create_token_pair, create_access_token
from app.core.config import settings

from app.utils.time import get_time_string
from app.utils.email_send import send_email

from app.uow.orm import UnitOfWork


class UserService:
    def __init__(
        self, 
        user_repo: UserRepository,
        app_service: AppService,
        uow: UnitOfWork
    ):
        self.user_repo = user_repo
        self.app_service = app_service
        self.uow = uow

    async def username_registered(self, username: str) -> bool:
        return await self.user_repo.username_registered(username)

    async def email_registered(self, email: EmailStr) -> bool:
        return await self.user_repo.email_registered(email)

    async def register_user(
        self, data: UserRequest, 
    ) -> UserDB:
        async with self.uow:
            username_used = await self.username_registered(data.username)
            if username_used:
                raise username_used_exception

            if data.email is not None:
                email_used = await self.email_registered(data.email)
                if email_used:
                    raise email_used_exception
                
            user = await self.uow.user_repo.register_user(data)
            await self.uow.commit()

        return user

    async def authenticate_user(
        self,
        username: str,
        password: str,
    ) -> Union[UserDB, False]:
        user = await self.get_user_by_username(username)

        if not user:
            verify_password(password, get_password_hash("dummypassword"))
            return False

        if not verify_password(password, user.hashed_password):
            return False

        return user

    async def login(
        self,
        username: str,
        password: str,
        bg_tasks: BackgroundTasks,
        request: Request,
        redis: Redis,
        sends_email: bool,
        access_secret_key: str,
        refresh_secret_key: str
    ) -> LoginResponse:
        user = await self.authenticate_user(username, password)

        if not user:
            raise incorrect_creds_exception

        email_body = settings.LOGIN_TEMPLATE % (
            request.client.host, get_time_string()
        )

        tokens = await create_token_pair(
            data={
                "sub": str(user.id), "roles": json.dumps(user.roles)
            }, 
            redis=redis,
            access_secret_key=access_secret_key,
            refresh_secret_key=refresh_secret_key
        )
        if user.email is not None and sends_email:
            bg_tasks.add_task(
                send_email,
                [str(user.email)],
                "Someone has logged into your account",
                email_body
        )
        return LoginResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            user_id=user.id,
        )

    async def logout(
        self, refresh_token: str, redis: Redis, secret_key: str
    ) -> dict[str, str]:
        try:
            payload = jwt.decode(
                refresh_token,
                secret_key,
                algorithms=settings.JWT_ALGORITHM,
            )
            jti = payload.get("jti")
            ttl = await redis.ttl(f"refresh_token:{jti}")
            if ttl > 0:
                await redis.set(f"blacklist:{jti}", "1", ex=ttl)
            await redis.delete(f"refresh_token:{jti}")

            return {"message": "Logout successful"}

        except DecodeError:
            raise invalid_refresh_token_exception

    async def set_role(
        self, user_id: UUID, role: UserRole, secret_key: str
    ) -> UserRoleResponse:
        async with self.uow:
            user = await self.uow.user_repo.get_user_by_id(user_id)

            if not user:
                raise user_not_found_exception

            if role.value in user.roles:
                raise already_has_role_exception

            user.roles = user.roles + [role.value]
            await self.uow.commit()

        access_token = create_access_token(
            data={
                "sub": str(user_id), "roles": json.dumps(user.roles)
            },
            secret_key=secret_key
        )
        return UserRoleResponse(
            acquired_role=role.value,
            username=user.username,
            new_access_token=access_token
        )

    async def update_user(
        self, user: UserDB, data: UserUpdate, 
    ):
        async with self.uow:
            if user.username == data.username:
                raise user_data_used_exception

            if await self.username_registered(data.username):
                raise username_used_exception
                
            data = data.model_dump(exclude_unset=True, exclude_none=True)
            user.sqlmodel_update(data)

            if "password" in data:
                user.hashed_password = get_password_hash(data["password"])

            await self.uow.commit()

        return user

    async def get_user_by_username(
        self, username: str
    ) -> Optional[UserDB]:
        user = await self.user_repo.get_user_by_username(username)

        if user is None:
            raise user_not_found_exception

        return user

    async def get_user_by_id(
        self, id: UUID
    ) -> Optional[UserDB]:
        user = await self.user_repo.get_user_by_id(id)

        if user is None:
            raise user_not_found_exception

        return user

    async def get_users(self, skip: int, limit: int) -> list[UserDB]:
        users = await self.user_repo.get_users(skip, limit)
        return users

    async def delete_user(
        self, 
        user_id: UUID, 
        redis: Redis
    ) -> None:
        async with self.uow:
            user = await self.uow.user_repo.get_user_by_id(user_id)

            if user is None:
                raise user_not_found_exception

            published_apps = await self.uow.app_repo.get_publisher_apps(
                user_id=user_id, public_only=False
                )

            for app in published_apps:
                await self.app_service.delete_app(app.id, self.uow)

            await redis.delete(f"user_tokens:{user_id}")
            await self.uow.session.delete(user)

            await self.uow.commit()
