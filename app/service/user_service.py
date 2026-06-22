from decimal import Decimal

from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.security import HTTPAuthorizationCredentials

from app.models.user import UserRequest, UserDB, UserUpdate
from app.models.token import LoginResponse, RefreshTokenRequest
from app.repo import user_repo
from app.core.exceptions import user_not_found_exception
from app.core.security import verify_password
from app.core.config import settings
from app.core.auth import create_token_pair, blacklist_token, revoke_refresh_token

async def register_user(
    data: UserRequest, session: AsyncSession
) -> UserDB:
    return await user_repo.register_user(data, session)


async def authenticate_user(
    username: str, password: str, session: AsyncSession
):
    user = await get_user(session, username=username)

    if not user:
        verify_password(password, settings.DUMMY_HASH)
        return False
    
    if not verify_password(password, user.hashed_password):
        return False
    
    return user


async def login(
    username: str, password: str, session: AsyncSession
):
    await authenticate_user(
        username, password, session
        )
    access_token, refresh_token = create_token_pair(username)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        username=username
        )


async def logout(
    refresh_request: RefreshTokenRequest | None, 
    credentials: HTTPAuthorizationCredentials
):
    access_token = credentials.credentials
    blacklist_token(access_token)

    # If refresh token provided, revoke it
    if refresh_request and refresh_request.refresh_token:
        revoke_refresh_token(refresh_request.refresh_token)

    return {"message": "Logout successful"}


async def top_up_balance(
    amount: Decimal, session: AsyncSession, user: UserDB
):
    return await user_repo.top_up_balance(
        amount, user, session
        )
        

async def update_user(
    username: str, data: UserUpdate, session: AsyncSession
):
    return await user_repo.update_user(username, data, session)


async def get_user(
    session: AsyncSession, username: str
):
    user = await user_repo.get_user(session, username=username)

    if user is None:
        raise user_not_found_exception

    return user


async def get_users(
    session: AsyncSession,
    skip: int, limit: int
) -> UserDB:
    return await user_repo.get_users(session, skip, limit)


async def delete_user(
    user: UserDB, session: AsyncSession
) -> dict[str, str]:
    return await user_repo.delete_user(user, session)
    