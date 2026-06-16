from decimal import Decimal

from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.user import UserRequest, UserDB, UserUpdate
from app.repo import user_repo

async def register_user(
        data: UserRequest, session: AsyncSession
        ) -> UserDB:
    return await user_repo.register_user(data, session)


async def increase_balance(
        amount: Decimal, session: AsyncSession, username: str
        ):
    return await user_repo.increase_balance(
        amount, username, session)


async def update_user(
        username: str, data: UserUpdate, session: AsyncSession
        ):
    return await user_repo.update_user(username, data, session)


async def get_user(
        username: str, session: AsyncSession
        ):
    return await user_repo.get_user(session, username=username)


async def get_users(
        search_query: str, session: AsyncSession
        ) -> UserDB:
    return await user_repo.get_users(search_query, session)


async def delete_user(
        username: str, session: AsyncSession
        ) -> dict[str, str]:
    return await user_repo.delete_user(username, session)
    