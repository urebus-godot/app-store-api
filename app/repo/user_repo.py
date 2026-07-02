from decimal import Decimal
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from pydantic import EmailStr
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload

from app.models.user import UserRequest, UserDB, UserUpdate, UserRole
from app.core.security import get_password_hash
from app.core.logging import logger


class AbstractUserRepository(ABC):
    @abstractmethod
    async def username_registered(
        self, username: str
    ) -> bool:
        pass

    @abstractmethod
    async def email_registered(
        self, email: EmailStr
    ) -> bool:
        pass

    @abstractmethod
    async def register_user(
        self, data: UserRequest
    ) -> UserDB:
        pass

    @abstractmethod
    async def top_up_balance(
        self, amount: Decimal, user: UserDB
    ) -> dict[str, str]:
        pass

    @abstractmethod
    async def become_publisher(
        self, user: UserDB
    ) -> dict[str, str]:
        pass

    @abstractmethod
    async def update_user(
        self, data: UserUpdate, user: UserDB
    ) -> UserDB:
        pass

    @abstractmethod
    async def get_user_by_username(
        self, username: str
    ) -> Optional[UserDB]:
        pass

    @abstractmethod
    async def get_user_by_id(self, id: UUID) -> Optional[UserDB]:
        pass

    @abstractmethod
    async def get_users(
        self, skip: int, limit: int
    ) -> UserDB:
        pass

    @abstractmethod
    async def delete_user(
        self, user: UserDB
    ) -> dict[str, str]:
        pass


class UserRepository(AbstractUserRepository):
    def __init__(self, session: AsyncSession):
        self.load_attrs = (
            selectinload(UserDB.published_apps), 
            selectinload(UserDB.purchased_apps), 
            selectinload(UserDB.cart), 
            selectinload(UserDB.reviews)
            )
        self.session = session

    async def username_registered(
        self, username: str
    ) -> bool:
        user = (await self.session.exec(
            select(UserDB).where(
            UserDB.username == username
            ).options(*self.load_attrs)
                )).one_or_none()
        return user is not None

    async def email_registered(
        self, email: EmailStr
    ) -> bool:
        user = (await self.session.exec(
            select(UserDB).where(
                UserDB.email == email
                ).options(*self.load_attrs)
        )).one_or_none()
        return user is not None

    async def register_user(
        self, data: UserRequest
    ) -> UserDB:
        user = UserDB(**data.model_dump())
        user.hashed_password = get_password_hash(data.password)

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def top_up_balance(
        self, amount: Decimal, user: UserDB
    ) -> dict[str, str]:
        user.balance += amount

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        
        return {"message": "Balance has been replenished"}

    async def become_publisher(
        self, user: UserDB
    ) -> dict[str, str]:
        user.roles = user.roles + [UserRole.PUBLISHER]

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        return {"message": "You have become a publisher"}

    async def update_user(
        self, data: UserUpdate, user: UserDB
    ) -> UserDB:
        data = data.model_dump(exclude_unset=True, exclude_none=True)
        user.sqlmodel_update(data)
        
        if "password" in data:
            user.hashed_password = get_password_hash(data["password"])

        self.session.add(user)
        await self.session.commit()
        #await self.session.refresh(user)
 
        return user

    async def get_user_by_username(
        self, username: str
    ) -> Optional[UserDB]:
        user = (await self.session.exec(
            select(UserDB).where(
                UserDB.username == username
                ).options(*self.load_attrs)
        )).one_or_none()
        return user

    async def get_user_by_id(self, id: UUID) -> Optional[UserDB]:
        user = (await self.session.exec(
            select(UserDB).where(
                UserDB.id == id
                ).options(*self.load_attrs)
        )).one_or_none()
        return user

    async def get_users(
        self, skip: int, limit: int
    ) -> UserDB:
        users = (await self.session.exec(
            select(UserDB).offset(skip).limit(limit).options(
                *self.load_attrs)
        )).all()
        return users

    async def delete_user(
        self, user: UserDB
    ) -> dict[str, str]:
        await self.session.delete(user)
        await self.session.commit()
        #await session.flush(user)

        return {"message": "User has been deleted"}