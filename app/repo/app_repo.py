from uuid import UUID
from typing import Optional
from datetime import datetime, timezone

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc
from sqlalchemy.orm import selectinload

from app.core.logging import logger

from app.models.app import AppDB
from app.base_models.app import (
    GameGenre,
    AppCategory
)
from app.schemas.app import AppRequest, GameRequest, AppUpdate
from app.base_models.app import (
    GameGenre,
    AppCategory
)
from app.models.file import AppArchive, AppCover, AppThumbnail
from app.models.purchase import PurchaseDB


class AppRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.public_app_conditions = (
            AppDB.public
            )
        self.load_attrs = (
            selectinload(AppDB.reviews),
            selectinload(AppDB.users_purchased),
            selectinload(AppDB.publisher),
        )

    async def upload_app(self, data: AppRequest, user_id: UUID) -> AppDB:
        app = AppDB(
            **data.model_dump(), 
            publisher_id=user_id
            )

        if isinstance(data, GameRequest):
            app.category = AppCategory.GAME
        else:
            app.category = AppCategory.APPLICATION
            app.genre = None

        self.session.add(app)

        return app

    async def update_app(
        self,
        data: AppUpdate,
        app: AppDB,
    ) -> AppDB:
        data = data.model_dump(exclude_unset=True, exclude_none=True)
        app.sqlmodel_update(data)

        return app

    async def update_app_rating(
        self, app: AppDB
    ) -> None:
        rating_sum = sum(review.rating for review in app.reviews)
        review_count = len(app.reviews)
        logger.info(f"{review_count = }; {rating_sum = }")
        if review_count > 0:
            app.rating = rating_sum / review_count
        else:
            app.rating = None

        logger.info(f"Calculated app rating: {app.rating}")

    async def get_app_archive(
        self, app_id: UUID
    ) -> Optional[AppArchive]:
        stmt = select(AppArchive).where(AppArchive.app_id == app_id)
        app_archive = (await self.session.exec(stmt)).one_or_none()

        return app_archive

    async def get_app_thumbnail(
        self, app_id: UUID
    ) -> Optional[AppThumbnail]:
        stmt = select(AppThumbnail).where(AppThumbnail.app_id == app_id)
        app_thumbnail = (await self.session.exec(stmt)).one_or_none()

        return app_thumbnail

    async def get_app_cover(
        self, cover_id: UUID
    ) -> Optional[AppCover]:
        stmt = select(AppCover).where(AppCover.id == cover_id)
        app_cover = (await self.session.exec(stmt)).one_or_none()
        return app_cover

    async def get_app_covers(
        self, app_id: UUID
    ) -> list[AppCover]:
        stmt = select(AppCover).where(AppCover.app_id == app_id)
        app_covers = (await self.session.exec(stmt)).all()
        return app_covers

    async def get_app(
        self, id: UUID
    ) -> AppDB:
        stmt = select(AppDB).where(AppDB.id == id)
        app = (
            await self.session.exec(stmt.options(*self.load_attrs))
        ).one_or_none()

        return app

    async def get_public_app(
        self, id: UUID
    ) -> AppDB:
        stmt = select(AppDB).where(
            AppDB.id == id,
            AppDB.public
            )

        app = (
            await self.session.exec(stmt.options(*self.load_attrs))
        ).one_or_none()

        return app

    async def get_apps(
        self,
        skip: int = 0,
        limit: Optional[int] = None,
        public_only: bool = True,
        order_by: Optional[str] = "published_at",
    ) -> list[AppDB]:
        stmt = (
            select(AppDB)
            .offset(skip)
            .options(*self.load_attrs)
        )

        if limit is not None:
            stmt = stmt.limit(limit)

        if public_only:
            stmt = stmt.where(AppDB.public)

        if order_by is not None:
            stmt = stmt.order_by(desc(AppDB.published_at))

        apps = (await self.session.exec(stmt)).all()

        return apps

    async def get_purchased_apps(self, user_id: UUID) -> list[AppDB]:
        apps = (
            await self.session.exec(
                select(AppDB)
                .where(
                    PurchaseDB.app_id == AppDB.id,
                    PurchaseDB.user_id == user_id,
                )
                .order_by(desc(AppDB.published_at))
            )
        ).all()
        return apps

    async def get_publisher_apps(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 0,
        public_only: Optional[bool] = True,
    ) -> list[AppDB]:
        stmt = (
            select(AppDB)
            .where(AppDB.publisher_id == user_id)
            .offset(skip)
            .order_by(desc(AppDB.published_at))
        )

        if public_only:
            stmt = stmt.where(*self.public_app_conditions)

        if limit > 0:
            stmt.limit(limit)

        publisher_apps = (
            await self.session.exec(stmt.options(*self.load_attrs))
        ).all()

        return publisher_apps

    async def get_games(
        self,
        genre: Optional[GameGenre],
        skip: int,
        limit: int,
        only_public: bool = True,
    ) -> list[AppDB]:
        stmt = (
            select(AppDB)
            .where(AppDB.category == AppCategory.GAME)
            .order_by(desc(AppDB.published_at))
            .offset(skip)
            .limit(limit)
        )

        if only_public:
            stmt.where(AppDB.public)

        games = (
            await self.session.exec(stmt.options(*self.load_attrs))
            ).all()

        return games

    async def get_top_games_genre(
        self, 
        genre: GameGenre,
        skip: int, limit: int
    ) -> list[AppDB]:
        games = (await self.session.exec(
            select(AppDB)
            .where(
                AppDB.category == "game",
                AppDB.genre == genre,
                AppDB.public
                ).order_by(
                    desc(AppDB.times_purchased)
                    ).limit(5).options(*self.load_attrs)
        )).all()

        return games

    async def get_top_games(
        self,
        skip: int, limit: int
    ) -> list[AppDB]:
        games = (await self.session.exec(
            select(AppDB)
            .where(
                AppDB.category == "game",
                AppDB.public
                )
            .order_by(
                desc(AppDB.times_purchased),
                desc(AppDB.rating)
                ).offset(skip).limit(limit)
                .options(*self.load_attrs)
        )).all()

        return games
