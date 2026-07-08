from uuid import UUID
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc
from sqlalchemy.orm import selectinload

from app.models.app import (
    AppRequest, GameRequest, AppDB, AppUpdate, 
    GameGenre, AppCategory)
from app.models.app_purchase import Purchase


class AppRepository:
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

        return app

    async def get_app(
        self, id: UUID, public: Optional[bool] = True
    ) -> AppDB:
        stmt = select(AppDB).where(AppDB.id == id)

        if public:
            stmt = stmt.where(AppDB.public)

        app = (await self.session.exec(
            stmt.options(*self.load_attrs)
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
        self, skip: int, limit: int,
        public_only: Optional[bool] = True,
        order_by: Optional[str] = "created_at"
    ) -> list[AppDB]:
        stmt = select(AppDB).offset(skip).limit(limit).order_by(
            desc(AppDB.published_at)
            )

        if public_only:
            stmt = stmt.where(AppDB.public)

        apps = (await self.session.exec(
            stmt.options(*self.load_attrs)
        )).all()

        return apps

    async def get_purchased_apps(self, user_id: UUID) -> list[AppDB]:
        apps = (await self.session.exec(
            select(AppDB).where(
                Purchase.app_id == AppDB.id, 
                Purchase.user_id == user_id
                ).order_by(desc(AppDB.published_at))
            )).all()
        return apps

    async def get_publisher_apps(
        self, skip: int, limit: int, user_id: UUID,
        public_only: Optional[bool] = True
    ) -> list[AppDB]:
        stmt = select(AppDB).where(
            AppDB.publisher_id == user_id
            ).offset(skip).limit(limit).order_by(desc(AppDB.published_at))

        if public_only:
            stmt = stmt.where(AppDB.public)
        
        publisher_apps = (await self.session.exec(
            stmt.options(*self.load_attrs)
        )).all()

        return publisher_apps

    async def get_games(
        self, genre: Optional[GameGenre],
        skip: int, limit: int,
        only_public: bool = True
    ) -> list[AppDB]:
        conditions = [AppDB.category == "game"]

        if genre is not None:
            conditions.append(AppDB.genre == genre)

        if only_public:
            conditions.append(AppDB.public)

        stmt = select(AppDB).where(*conditions).order_by(
            desc(AppDB.published_at)
            ).offset(skip).limit(limit)

        games = (await self.session.exec(
            stmt.options(*self.load_attrs)
        )).all()

        return games

    async def delete_app(
        self,
        app: AppDB
    ) -> None:
        await self.session.delete(app)
        await self.session.commit()
