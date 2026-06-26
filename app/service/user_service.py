from decimal import Decimal

from fastapi.security import HTTPAuthorizationCredentials

from app.models.user import UserRequest, UserDB, UserUpdate, UserRole
from app.models.token import LoginResponse, RefreshTokenRequest, TokenResponse
from app.repo.user_repo import UserRepository
from app.core.exceptions import (
    user_not_found_exception, 
    email_used_exception,
    username_used_exception,
    already_has_role_exception,
    incorrect_creds_exception)
from app.core.security import verify_password, get_password_hash
from app.core.auth import (
    create_token_pair, blacklist_token, revoke_refresh_token)
from app.core.logging import logger


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register_user(
        self, data: UserRequest
    ) -> UserDB:
        username_used = await self.user_repo.username_registered(data.username)
        if username_used:
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
        self, username: str, password: str, 
    ):
        user = await self.authenticate_user(
            username, password
            )

        if not user:
            raise incorrect_creds_exception
        
        access_token, refresh_token = create_token_pair(username)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            username=username
            )
        return TokenResponse(access_token=access_token)

    async def logout(
        self, refresh_request: RefreshTokenRequest | None, 
        credentials: HTTPAuthorizationCredentials
    ):
        access_token = credentials.credentials
        await blacklist_token(access_token)

        # If refresh token provided, revoke it
        if refresh_request and refresh_request.refresh_token:
            await revoke_refresh_token(refresh_request.refresh_token)

        return {"message": "Logout successful"}

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
        return await self.user_repo.update_user(
            data=data, user=user
            )

    async def get_user(
        self, username: str
    ):
        user = await self.user_repo.get_user(username=username)

        if user is None:
            raise user_not_found_exception

        return user

    async def get_users(
        self,
        skip: int, limit: int
    ) -> UserDB:
        return await self.user_repo.get_users(skip, limit)

    async def delete_user(
        self, user: UserDB, 
    ) -> dict[str, str]:
        return await self.user_repo.delete_user(user)
        