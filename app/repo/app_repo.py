from uuid import UUID
from typing import Optional
from decimal import Decimal
from abc import ABC, abstractmethod

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload

from app.models.app import (
    AppRequest, GameRequest, AppDB, AppUpdate, 
    GameGenre, AppCategory)
from app.models.app_purchase import Purchase
from app.models.user import UserDB
from app.core.logging import logger


class AbstractAppRepository(ABC):
    @abstractmethod
    async def upload_app(
        self, data: AppRequest, user_id: UUID
    ) -> AppDB:
        pass

    @abstractmethod
    async def update_app(
        self, data: AppUpdate,
        id: Optional[UUID] = None,
        app: Optional[AppDB] = None,
    ) -> AppDB:
        pass

    @abstractmethod
    async def get_app(
        self, id: UUID
    ) -> AppDB:
        pass

    @abstractmethod
    async def get_app_by_publisher(
        self, publisher_id: UUID, app_id: UUID
    ) -> Optional[AppDB]:
        pass

    @abstractmethod
    async def get_apps(
        self, skip: int, limit: int
    ) -> list[AppDB]:
        pass

    @abstractmethod
    async def get_purchased_apps(self, user: UserDB) -> list[AppDB]:
        pass

    @abstractmethod
    async def get_publisher_apps(
        self, skip: int, limit: int, user_id: UUID
    ) -> list[AppDB]:
        pass

    @abstractmethod
    async def get_games(
        self, genre: GameGenre,
        skip: int, limit: int
    ) -> list[AppDB]:
        pass

    @abstractmethod
    async def delete_app(
        self,
        id: Optional[UUID] = None,
        app: Optional[AppDB] = None
    ) -> dict[str, str]:
        pass


class AppRepository(AbstractAppRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.load_attrs = (
            selectinload(AppDB.reviews), 
            selectinload(AppDB.users_purchased),
            selectinload(AppDB.publisher)
            )

    async def upload_app(
        self, data: AppRequest, user_id: UUID
    ) -> AppDB:
        app = AppDB(**data.model_dump(), publisher_id=user_id)
        
        if isinstance(data, GameRequest):
            app.category = AppCategory.GAME
        else:
            app.category = AppCategory.APPLICATION
            app.genre = None
            
        self.session.add(app)
        await self.session.commit()

        app = (await self.session.exec(
            select(AppDB).where(AppDB.id == app.id).options(*self.load_attrs)
            )).one()
        
        return app

    async def update_app(
        self, data: AppUpdate,
        id: Optional[UUID] = None,
        app: Optional[AppDB] = None,
    ) -> AppDB:
        if app is None:
            app = await self.get_app(id)

        data = data.model_dump(exclude_unset=True, exclude_none=True)

        app.sqlmodel_update(data)

        self.session.add(app)
        await self.session.commit()
        await self.session.refresh(app)

        return app

    async def get_app(
        self, id: UUID
    ) -> AppDB:
        app = (await self.session.exec(
            select(AppDB).where(AppDB.id == id).options(*self.load_attrs)
        )).one_or_none()
        return app

    async def get_app_by_publisher(
        self, publisher_id: UUID, app_id: UUID
    ) -> Optional[AppDB]:
        app = (await self.session.exec(
            select(AppDB).where(
                AppDB.id == app_id, 
                AppDB.publisher_id == publisher_id
                )
        )).first()
        return app

    async def get_apps(
        self, skip: int, limit: int
    ) -> list[AppDB]:
        apps = (await self.session.exec(
            select(AppDB).offset(skip).limit(limit).options(*self.load_attrs)
        )).all()
        return apps

    async def get_purchased_apps(self, user_id: UUID) -> list[AppDB]:
        apps = (await self.session.exec(
            select(AppDB).where(
                Purchase.app_id == AppDB.id, 
                Purchase.user_id == user_id
                )
            )).all()
        return apps

    async def get_publisher_apps(
        self, skip: int, limit: int, user_id: UUID
    ) -> list[AppDB]:
        publisher_apps = (await self.session.exec(
            select(AppDB).where(
                AppDB.publisher_id == user_id
                ).offset(skip).limit(limit).options(*self.load_attrs)
        )).all()
        return publisher_apps

    async def get_games(
        self, genre: Optional[GameGenre],
        skip: int, limit: int
    ) -> list[AppDB]:
        if genre is not None:
            games = (await self.session.exec(
                select(AppDB).where(
                    AppDB.genre == genre,
                    AppDB.category == "game"
                    ).offset(skip).limit(limit).options(*self.load_attrs)
            )).all()
        else:
            games = (await self.session.exec(
                select(AppDB).where(
                    AppDB.category == "game"
                    ).offset(skip).limit(limit).options(*self.load_attrs)
            )).all()
        return games

    async def delete_app(
        self,
        id: Optional[UUID] = None,
        app: Optional[AppDB] = None
    ) -> dict[str, str]:
        if app is None:
            app = await self.get_app(id)

        await self.session.delete(app)
        await self.session.commit()

        return {"detail": "App has been deleted"}