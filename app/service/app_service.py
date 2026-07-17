from uuid import UUID, uuid4
from typing import Optional
import pathlib
import os

from fastapi import UploadFile, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import logger
from app.core.exceptions import (
    app_not_found_exception,
    no_rights_exception,
    app_not_purchased_exception,
    invalid_file_exception
)
from app.core.config import settings
from app.service.user_service import UserService
from app.models.app import AppRequest, AppUpdate, GameGenre, AppDB
from app.models.user import UserDB
from app.repo.app_repo import AppRepository
from app.utils.search import filter_apps


class AppService:
    def __init__(self, app_repo: AppRepository, user_service: UserService):
        self.app_repo = app_repo
        self.user_service = user_service

    async def upload_app(
        self, data: AppRequest, user: UserDB
    ) -> AppDB:
        app = await self.app_repo.upload_app(data, user.id)
        return app

    async def update_app(
        self, id: UUID, user_id: UUID, data: AppUpdate
    ) -> AppDB:
        app = await self.get_app(id, False)

        if app.publisher_id != user_id:
            raise no_rights_exception

        app = await self.app_repo.update_app(data, app=app)

        return app

    async def upload_app_archive(
        self, 
        session: AsyncSession, 
        file: UploadFile, 
        app_id: UUID, user_id: UUID
    ):
        app = await self.get_app(app_id, False)
        logger.info(f"Start uploading archive for app: {app_id}")

        if not app.public and app.publisher_id != user_id:
            raise app_not_found_exception

        if app.publisher_id != user_id:
            raise no_rights_exception

        extension = os.path.splitext(file.filename)[1]
        logger.info(f"File extension: {extension}")
        
        if extension not in settings.ARCHIVE_EXTENSIONS:
            raise invalid_file_exception

        filename = f"{app_id}{extension}"

        os.makedirs(settings.ARCHIVE_PATH, exist_ok=True)
        file_path = os.path.join(settings.ARCHIVE_PATH, filename)

        logger.info(f"Path for file: {file_path}")

        with open(file_path, "wb") as buffer:
            logger.info("Start writing to disk")
            while chunk := file.file.read(1024 * 1024):
                buffer.write(chunk)
                logger.info(
                    f"Wrote chunk to buffer: {chunk[:30]}..."
                    f"Length: {len(chunk)}"
                    )

        app.archive_path = file_path
        await session.commit()
        logger.info(f"Committed. App archive path is now: {app.archive_path}")

    async def upload_app_cover(
        self,
        session: AsyncSession, 
        file: UploadFile, 
        app_id: UUID, user_id: UUID
    ):
        app = await self.get_app(app_id, False)
        logger.info(f"Start uploading archive for app: {app_id}")

        if not app.public and app.publisher_id != user_id:
            raise app_not_found_exception

        if app.publisher_id != user_id:
            raise no_rights_exception

        extension = os.path.splitext(file.filename)[1]
        logger.info(f"File extension: {extension}")
        
        if extension not in settings.IMAGE_EXTENSIONS:
            raise invalid_file_exception

        filename = f"{app_id}{extension}"
        path = f"{settings.STATIC_BASE_PATH}/covers"

        os.makedirs(path, exist_ok=True)
        file_path = os.path.join(path, filename)

        logger.info(f"Path for file: {file_path}")

        with open(file_path, "wb") as buffer:
            logger.info("Start writing to disk")
            while chunk := file.file.read(1024 * 1024):
                buffer.write(chunk)
                logger.info(
                    f"Wrote chunk to buffer: {chunk[:30]}..."
                    f"Length: {len(chunk)}"
                    )

        app.archive_path = file_path
        await session.commit()
        logger.info(f"Committed. App archive path is now: {app.archive_path}")

    async def get_app_archive_path(
        self, app_id: UUID, user: UserDB
    ):
        app = await self.get_app(app_id)

        if not (app in user.purchased_apps or app.publisher_id == user.id):
            raise app_not_purchased_exception

        archive_path = app.archive_path

        if archive_path is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "Application has no archive file"
            )
        logger.info(f"App's archive path: {app.archive_path}")
        return archive_path
        
    async def get_app(self, id: UUID, public_only: bool = True) -> AppDB:
        app = await self.app_repo.get_app(id, public_only)

        if not app:
            raise app_not_found_exception

        return app

    async def get_apps(
        self, skip: int, limit: int, search_query: Optional[str] = None
    ) -> list[AppDB]:
        apps = await self.app_repo.get_apps(skip, limit)

        if search_query is not None:
            apps = filter_apps(apps, search_query)

        return apps

    async def get_purchased_apps(self, user_id: UUID) -> list[AppDB]:
        purchased_apps = await self.app_repo.get_purchased_apps(user_id)
        return purchased_apps

    async def get_publisher_apps(
        self, 
        skip: int, limit: int, 
        user_id: UUID, 
        public_only: bool = True
    ) -> list[AppDB]:
        await self.user_service.get_user_by_id(user_id)

        publisher_apps = await self.app_repo.get_publisher_apps(
            skip=skip, limit=limit, user_id=user_id, public_only=public_only
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
        games = await self.app_repo.get_games(genre, skip, limit, only_public)

        if search_query is not None:
            games = filter_apps(games, search_query)

        return games

    async def get_top_games(self, genre: Optional[GameGenre]) -> list[AppDB]:
        if genre:
            games = await self.app_repo.get_top_games_genre(genre)
        else:
            games = await self.app_repo.get_top_games()
        return games

    async def delete_app(
        self, id: UUID, user_id: UUID
    ) -> None:
            app = await self.get_app(id)

            if not app.publisher_id == user_id:
                raise no_rights_exception

            await self.app_repo.delete_app(app)
