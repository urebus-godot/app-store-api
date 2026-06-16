from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.user import UserRequest, UserDB

async def register_user(
        user: UserRequest, session: AsyncSession
        ) -> UserDB:
    pass


async def get_users(
        user: UserRequest, session: AsyncSession
        ) -> UserDB:
    pass


async def delete_user(
        user: UserRequest, session: AsyncSession
        ) -> UserDB:
    pass