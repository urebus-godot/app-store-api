from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import EmailStr
from jwt.exceptions import DecodeError
import jwt

from app.models.user import UserRequest, UserDB, UserUpdate, UserRole
from app.models.token import LoginResponse, RefreshTokenRequest, TokenResponse
from app.repo.user_repo import UserRepository
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
from app.core.auth import create_token_pair
from app.core.logging import logger
from app.core.config import settings
from app.db.redis import Redis


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def username_registered(self, username: str) -> bool:
        return await self.user_repo.username_registered(username)

    async def email_registered(self, email: EmailStr) -> bool:
        return await self.user_repo.email_registered(email)

    async def register_user(
        self, data: UserRequest
    ) -> UserDB:
        if await self.username_registered(data.username):
            raise username_used_exception

        if data.email is not None:
            email_used = await self.user_repo.email_registered(data.email)
            if email_used:
                raise email_used_exception
            
        return await self.user_repo.register_user(data)

    async def authenticate_user(
        self, username: str, password: str, 
    ) -> UserDB | False:
        user = await self.get_user(username=username)
        logger.info(f"User found: {user.username}")

        if not user:
            verify_password(password, get_password_hash("dummypassword"))
            return False
        
        if not verify_password(password, user.hashed_password):
            return False
        
        return user

    async def login(
        self, username: str, password: str, redis: Redis
    ) -> LoginResponse:
        user = await self.authenticate_user(
            username, password
            )

        if not user:
            raise incorrect_creds_exception
        
        tokens = await create_token_pair(str(user.id), redis)

        return LoginResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            user_id=user.id
            )

    async def logout(
        self, 
        refresh_token: str, 
        redis: Redis
    ) -> dict[str, str]:
        try:
            payload = jwt.decode(
                refresh_token, 
                settings.SECRET_KEY, 
                algorithms=settings.JWT_ALGORITHM
                )
            jti = payload.get("jti")
            ttl = await redis.ttl(f"refresh_token:{jti}")
            logger.info(f"{payload = }")
            logger.info(f"{ttl = }")
            if ttl > 0:
                await redis.set(f"blacklisted_tokens:{jti}", "1", ex=ttl)
            await redis.delete(f"refresh_token:{jti}")

            return {"message": "Logout successful"}

        except DecodeError as e:
            logger.info(f"Exception = {e}")
            raise invalid_refresh_token_exception

    async def top_up_balance(
        self, amount: Decimal, user: UserDB
    ):
        return await self.user_repo.top_up_balance(
            amount, user
            )

    async def become_publisher(
        self, user: UserDB, 
    ) -> dict[str, str]:
        if UserRole.PUBLISHER in user.roles:
            raise already_has_role_exception
        return await self.user_repo.become_publisher(user)

    async def update_user(
        self, user: UserDB, data: UserUpdate, 
    ):
        if user.username == data.username or user.email == data.email:
            raise user_data_used_exception
        
        if await self.username_registered(data.username):
            raise username_used_exception

        if data.email is not None:
            if await self.email_registered(data.email):
                raise email_used_exception
        
        return await self.user_repo.update_user(
            data=data, user=user
            )

    async def get_user(
        self, 
        username: Optional[str] = None, 
        id: Optional[UUID] = None
    ) -> Optional[UserDB]:
        if username is not None:
            user = await self.user_repo.get_user_by_username(username)
        if id is not None:
            user = await self.user_repo.get_user_by_id(id)
        if user is None:
            raise user_not_found_exception

        return user

    async def get_users(
        self,
        skip: int, limit: int
    ) -> list[UserDB]:
        users = await self.user_repo.get_users(skip, limit)
        return users

    async def delete_user(
        self, user: UserDB, 
    ) -> None:
        await self.user_repo.delete_user(user)
        