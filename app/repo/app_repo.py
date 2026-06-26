from uuid import UUID
from typing import Optional
from decimal import Decimal
from abc import ABC, abstractmethod

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from fastapi import UploadFile

from app.models.app import (
    AppRequest, GameRequest, AppDB, AppUpdate, 
    GameGenre, AppCategory)
from app.models.user import UserDB


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
    async def get_apps(
        self, skip: int, limit: int
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

    async def upload_app(
        self, data: AppRequest, user_id: UUID
    ) -> AppDB:
        app = AppDB(
                **data.model_dump(),
                publisher_id=user_id
            )
        
        if isinstance(data, GameRequest):
            app.category = AppCategory.GAME
        else:
            app.category = AppCategory.APPLICATION
            
        self.session.add(app)
        await self.session.commit()
        await self.session.refresh(app)
        
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
            select(AppDB).where(AppDB.id == id)
        )).one_or_none()
        return app

    async def get_apps(
        self, skip: int, limit: int
    ) -> list[AppDB]:
        apps = (await self.session.exec(
            select(AppDB).offset(skip).limit(limit)
        )).all()
        return apps

    async def get_games(
        self, genre: Optional[GameGenre],
        skip: int, limit: int
    ) -> list[AppDB]:
        if genre is not None:
            games = (await self.session.exec(
                select(AppDB).where(
                    AppDB.genre == genre,
                    AppDB.category == "game"
                    ).offset(skip).limit(limit)
            )).all()
        else:
            games = (await self.session.exec(
                select(AppDB).where(
                    AppDB.category == "game"
                    ).offset(skip).limit(limit)
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
        #await self.session.flush(app)

        return {"detail": "App has been deleted"}