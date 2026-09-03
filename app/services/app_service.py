from uuid import UUID
from typing import Optional
import logging

from fastapi import HTTPException, status, BackgroundTasks

from app.core.config import settings
from app.core.exceptions import (
    app_not_found_exception,
    no_rights_exception,
    user_not_found_exception
)

from app.schemas.app import (
    AppRequest, AppUpdate, GameUpdate, 
    )
from app.models.app import GameGenre, AppDB

from app.services.media_service import MediaService

from app.utils.search import format_keywords

from app.uow.orm import UnitOfWork

from app.storage.protocol import ObjectStorage

logger = logging.getLogger("services.app")


class AppService:
    def __init__(
        self, 
        media_service: MediaService,
        uow: UnitOfWork,
        storage: ObjectStorage
    ):
        self.uow = uow
        self.storage = storage
        self.media_service = media_service

    async def upload_app(
        self, data: AppRequest, publisher_id: UUID
    ) -> AppDB:
        async with self.uow:
            app = await self.uow.app_repo.upload_app(data, publisher_id)
            await self.uow.commit()

        return app

    async def update_app(
        self, id: UUID, user_id: UUID, data: AppUpdate
    ) -> AppDB:
        async with self.uow:
            app = await self.uow.app_repo.get_app(id)

            if app is None:
                raise app_not_found_exception

            if app.publisher_id != user_id:
                raise no_rights_exception

            if isinstance(data, GameUpdate) and app.category == "application":
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "This app is not game"
                )

            app = await self.uow.app_repo.update_app(data, app)
            await self.uow.commit()

        return app

    async def get_app(self, id: UUID) -> AppDB:
        async with self.uow:
            app = await self.uow.app_repo.get_public_app(id)

            if not app:
                raise app_not_found_exception

            return app

    async def get_apps(
        self, 
        skip: int, 
        limit: Optional[int] = None, 
        search_query: Optional[str] = None
    ) -> list[AppDB]:
        async with self.uow:
            if search_query is None:
                apps = await self.uow.app_repo.get_apps(skip, limit)
            else:
                apps = await self.uow.app_repo.get_apps_by_keywords(
                    keywords=format_keywords(search_query.split()),
                    skip=skip, limit=limit
                    )

        return apps

    async def get_purchased_apps(self, user_id: UUID) -> list[AppDB]:
        async with self.uow:
            purchased_apps = await self.uow.app_repo.get_purchased_apps(
                user_id
            )
        return purchased_apps

    async def get_publisher_apps(
        self, 
        skip: int, limit: int, 
        user_id: UUID, 
        public_only: bool = True
    ) -> list[AppDB]:
        async with self.uow:
            user = await self.uow.user_repo.get_user_by_id(user_id)

            if user is None:
                raise user_not_found_exception

            publisher_apps = await self.uow.app_repo.get_publisher_apps(
                skip=skip, 
                limit=limit,
                user_id=user_id, 
                public_only=public_only
            )

        return publisher_apps

    async def get_games(
        self,
        skip: int,
        limit: int,
        search_query: Optional[str] = None,
        genre: Optional[GameGenre] = None,
        only_public: bool = True,
    ) -> list[AppDB]:
        async with self.uow:
            if search_query is None:
                games = await self.uow.app_repo.get_games(
                    genre=genre, 
                    skip=skip, limit=limit, 
                    only_public=only_public
                    )
            else:
                games = await self.uow.app_repo.get_games_by_keywords(
                    genre=genre, 
                    keywords=format_keywords(search_query.split()), 
                    skip=skip, limit=limit
                    )

        return games

    async def get_top_games(
        self
    ) -> list[AppDB]:
        async with self.uow:
            games = await self.uow.app_repo.get_top_games(0, 10)
        return games

    async def get_top_games_genre(
        self, genre: Optional[GameGenre]
    ) -> list[AppDB]:
        async with self.uow:
            games = await self.uow.app_repo.get_top_games_genre(genre, 0, 10)
        return games

    async def delete_app(
        self, id: UUID
    ) -> None:
        raise NotImplementedError()
        app = await self.uow.app_repo.get_app(id)

        if app is None:
            return

        await self.uow.delete(app)

    async def delete_app_by_user(
        self, id: UUID, user_id: UUID, bg_tasks: BackgroundTasks
    ) -> None:
        async with self.uow:
            app = await self.uow.app_repo.get_app(id)

            if app is None:
                raise app_not_found_exception
            
            if not app.publisher_id == user_id:
                raise no_rights_exception
            logger.info(f"\n\n{app.archive_key}\n\n")
            if app.archive_key is not None:
                bg_tasks.add_task(
                    self.storage.delete_object,
                    settings.APP_ARCHIVE_BUCKET,
                    app.archive_key
                )

            if app.icon_key is not None:
                bg_tasks.add_task(
                    self.storage.delete_image_variants,
                    settings.APP_ICON_BUCKET,
                    app.icon_key
                )

            logger.info("Adding delete_app_covers task")

            bg_tasks.add_task(
                self.media_service.delete_app_covers,
                id
            )
            await self.uow.delete(app)
            await self.uow.commit()
