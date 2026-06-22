from decimal import Decimal

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models.user import UserRequest, UserDB, UserUpdate
from app.core.security import get_password_hash

async def register_user(
    data: UserRequest, session: AsyncSession
) -> UserDB:
    user = UserDB.model_validate(data)
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


async def top_up_balance(
    amount: Decimal, user: UserDB, session: AsyncSession
):
    user.balance += amount

    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    return {"message": "Balance has been replenished"}


async def update_user(
    data: UserUpdate, session: AsyncSession, user: UserDB
):
    data = data.model_dump(exclude_unset=True, exclude_none=True)
    user.sqlmodel_update(data)

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


async def get_user(
    session: AsyncSession, username: str
):
    user = (await session.exec(
        select(UserDB).where(UserDB.username == username)
    )).one_or_none()

    return user


async def get_users(
    skip: int, limit: int, session: AsyncSession
) -> UserDB:
    users = (await session.exec(
        select(UserDB).offset(skip).limit(limit)
    ))
    return users


async def delete_user(
    user: UserDB, session: AsyncSession
) -> dict[str, str]:
    await session.delete(user)
    await session.flush(user)

    return {"message": "User has been deleted"}