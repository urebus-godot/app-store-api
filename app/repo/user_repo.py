from typing import Optional
from uuid import UUID

from pydantic import EmailStr
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc
from sqlalchemy.orm import selectinload

from app.models.user import UserDB
from app.schemas.user import UserRequest, UserRole

from app.core.security import get_password_hash


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.load_attrs = (
            selectinload(UserDB.published_apps),
            selectinload(UserDB.purchased_apps),
            selectinload(UserDB.cart),
            selectinload(UserDB.reviews),
        )
        self.session = session

    async def username_registered(self, username: str) -> bool:
        user = (
            await self.session.exec(
                select(UserDB)
                .where(UserDB.username == username)
                .options(*self.load_attrs)
            )
        ).one_or_none()

        return user is not None

    async def email_registered(self, email: EmailStr) -> bool:
        user = (
            await self.session.exec(
                select(UserDB)
                .where(UserDB.email == email)
                .options(*self.load_attrs)
            )
        ).one_or_none()
        return user is not None

    async def register_user(self, data: UserRequest) -> UserDB:
        user = UserDB(
            **data.model_dump()
            )
        user.hashed_password = get_password_hash(data.password)

        self.session.add(user)

        return user

    async def get_user_by_username(self, username: str) -> Optional[UserDB]:
        user = (
            await self.session.exec(
                select(UserDB)
                .where(UserDB.username == username)
                .options(*self.load_attrs)
            )
        ).one_or_none()
        return user

    async def get_user_by_id(
        self, id: UUID,
        for_update: bool = False
    ) -> Optional[UserDB]:
        stmt =  (
            select(UserDB)
            .where(UserDB.id == id)
            .options(*self.load_attrs)
                )
        if for_update:
            stmt = stmt.with_for_update()
            
        user = (await self.session.exec(stmt)).one_or_none()

        return user

    async def get_users(self, skip: int, limit: int) -> list[UserDB]:
        users = (
            await self.session.exec(
                select(UserDB)
                .offset(skip)
                .limit(limit)
                .order_by(desc(UserDB.registered_at))
                .options(*self.load_attrs)
            )
        ).all()

        return users

    async def delete_user(self, user: UserDB) -> None:
        await self.session.delete(user)
