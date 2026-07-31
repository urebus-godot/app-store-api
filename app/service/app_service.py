from uuid import UUID, uuid4
from typing import Optional
import asyncio
import os

from fastapi import UploadFile, HTTPException, status
from redis.asyncio import Redis

from app.core.logging import logger
from app.core.exceptions import (
    app_not_found_exception,
    no_rights_exception,
    app_not_purchased_exception,
    invalid_file_exception,
    file_too_large_exception,
    app_cover_not_found_exception,
    user_not_found_exception
)
from app.core.config import settings
from app.bg_tasks import celery_tasks

from app.repo.user_repo import UserRepository

from app.models.app import GameGenre, AppDB
from app.schemas.app import (
    AppRequest, AppUpdate, GameUpdate, 
    )
from app.models.user import UserDB
from app.models.file import AppArchive, AppCover, AppThumbnail

from app.repo.app_repo import AppRepository
from app.repo.purchase_repo import PurchaseRepository

from app.utils.search import filter_apps
from app.utils.files import write_file, to_megabytes

from app.uow.orm import UnitOfWork


class AppService:
    def __init__(
            self, 
            app_repo: AppRepository, 
            user_repo: UserRepository,
            purchase_repo: PurchaseRepository
            ):
        self.app_repo = app_repo
        self.user_repo = user_repo
        self.purchase_repo = purchase_repo

    async def upload_app(
        self, data: AppRequest, user: UserDB, uow: UnitOfWork
    ) -> AppDB:
        async with uow:
            app = await uow.app_repo.upload_app(data, user.id)
            return app

    async def update_app(
        self, id: UUID, user_id: UUID, data: AppUpdate, uow: UnitOfWork
    ) -> AppDB:
        async with uow:
            app = await uow.app_repo.get_app(id)

            if app is None:
                raise app_not_found_exception

            if app.publisher_id != user_id:
                raise no_rights_exception

            if isinstance(data, GameUpdate) and app.category == "application":
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "This app is not game"
                )

            app = await uow.app_repo.update_app(data, app)

            return app

    async def update_app_rating(
        self, app_id: UUID, uow: UnitOfWork
    ) -> None:
        logger.info("Start calculating app rating...")
        app = await uow.app_repo.get_app(app_id)
        await uow.app_repo.update_app_rating(app)

        logger.info(f"New app rating: {app.rating}")

    async def upload_app_archive(
        self, 
        uow: UnitOfWork, 
        file: UploadFile, 
        app_id: UUID, user_id: UUID
    ) -> AppArchive:
        async with uow:
            app = await self.get_app(app_id)
            logger.info(f"Start uploading archive for app: {app_id}")

            if not app.public and app.publisher_id != user_id:
                raise app_not_found_exception

            if app.publisher_id != user_id:
                raise no_rights_exception

            file_size_mb = to_megabytes(file.size)
            if file_size_mb > settings.MAX_APP_ARCHIVE_SIZE_MB:
                raise file_too_large_exception

            extension = os.path.splitext(file.filename)[1]
  
            if extension not in settings.ARCHIVE_EXTENSIONS:
                raise invalid_file_exception

            filename = f"{app_id}{extension}"
            await asyncio.to_thread(
                write_file,
                file, filename, settings.APP_ARCHIVE_PATH
            )

            app_archive = await uow.app_repo.get_app_archive(app_id)
            
            logger.info(f"{ app_archive = }")

            if app_archive is None:
                app_archive = AppArchive(
                    filename=file.filename, 
                    app_id=app_id
                    )
                uow.session.add(app_archive)
                logger.info("Created new app archive")

            app_archive.filename = file.filename

            logger.info(
                "Committing. App archive path is now: "
                f"{settings.APP_ARCHIVE_PATH / str(app_archive.app_id)}"
                )
            return app_archive

    async def get_app_archive(
        self, app_id: UUID, user_id: UUID
    ) -> AppArchive:
        app = await self.get_app(app_id)
        app_purchased = await self.purchase_repo.user_purchased_app(
            user_id, app_id
            )

        if not (app_purchased or app.publisher_id == user_id):
            raise app_not_purchased_exception

        app_archive = await self.app_repo.get_app_archive(app_id)

        if app_archive is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "Archive of app not found"
            )

        return app_archive

    async def remove_app_archive(
        self, id: UUID, uow: UnitOfWork
    ) -> None:
        app_archive = await uow.app_repo.get_app_archive(id)
        if app_archive is not None:
            ext = os.path.splitext(app_archive.filename)[1]
            filename = f"{id}{ext}"
            app_archive_path = settings.APP_ARCHIVE_PATH / filename
            os.remove(app_archive_path)
            await uow.session.delete(app_archive)

    async def upload_app_thumbnail(
        self, 
        uow: UnitOfWork, 
        file: UploadFile, 
        app_id: UUID, user_id: UUID
    ) -> AppThumbnail:
        async with uow:
            app = await self.get_app(app_id)
            logger.info(f"Start uploading archive for app: {app_id}")

            if not app.public and app.publisher_id != user_id:
                raise app_not_found_exception

            if app.publisher_id != user_id:
                raise no_rights_exception
            
            extension = os.path.splitext(file.filename)[1]
            if extension not in settings.IMAGE_EXTENSIONS:
                raise invalid_file_exception

            file_size_mb = to_megabytes(file.size)
            if file_size_mb > settings.MAX_PROFILE_PICTURE_SIZE_MB:
                raise file_too_large_exception

            filename = f"{app_id}{extension}"
            file_path = settings.APP_THUMBNAIL_PATH / filename

            await asyncio.to_thread(
                write_file, 
                file, filename, settings.APP_THUMBNAIL_PATH
                )
            celery_tasks.process_image.delay(
                str(file_path), (128, 128), 85
                )

            app_thumbnail = await uow.app_repo.get_app_thumbnail(app_id)

            if app_thumbnail is None:
                app_thumbnail = AppThumbnail(
                    app_id=app_id,
                    extension=extension
                )
                uow.session.add(app_thumbnail)

            app_thumbnail.extension = extension

            return app_thumbnail

    async def remove_app_thumbnail(
        self, app_id: UUID, uow: UnitOfWork
    ) -> None:
        app_thumbnail = await uow.app_repo.get_app_thumbnail(app_id)

        if app_thumbnail is None:
            return

        await uow.session.delete(app_thumbnail)

        filename = f"{app_id}{app_thumbnail.extension}"
        thumbnail_path = (
            settings.APP_THUMBNAIL_PATH / filename
            )
        os.remove(thumbnail_path)
        await uow.session.delete(app_thumbnail)
        
    async def upload_app_cover(
        self,
        uow: UnitOfWork, 
        file: UploadFile, 
        app_id: UUID, user_id: UUID
    ) -> AppCover:
        async with uow:
            app = await self.get_app(app_id)
            logger.info(f"Start uploading archive for app: {app_id}")

            if not app.public and app.publisher_id != user_id:
                raise app_not_found_exception

            if app.publisher_id != user_id:
                raise no_rights_exception

            extension = os.path.splitext(file.filename)[1]
            logger.info(f"File extension: {extension}")

            if extension not in settings.IMAGE_EXTENSIONS:
                raise invalid_file_exception

            file_size_mb = to_megabytes(file.size)
            if file_size_mb > settings.MAX_APP_COVER_SIZE_MB:
                raise file_too_large_exception
            
            id = uuid4()
            app_cover = AppCover(
                id=id, 
                app_id=app_id, 
                extension=extension
                )
            filename = f"{id}{extension}"
            file_path = settings.APP_COVER_PATH / filename

            await asyncio.to_thread(
                write_file,
                file, filename, settings.APP_COVER_PATH
                )
            celery_tasks.process_image.delay(
                str(file_path), (1280, 720)
                )

            uow.session.add(app_cover)

            logger.info(f"Committed. App cover paths is now: {file_path}")

            return app_cover

    async def get_app_covers(
        self, 
        app_id: UUID,
        uow: UnitOfWork
    ) -> list[AppCover]:
        logger.info(f"\n\n\n {uow.__dict__} \n\n\n")
        app = await self.app_repo.get_public_app(app_id)

        if app is None:
            raise app_not_found_exception
        
        app_covers = await self.app_repo.get_app_covers(app_id)

        return app_covers

    async def remove_app_cover(
        self,
        cover_id: UUID,
        user_id: UUID,
        uow: UnitOfWork
    ) -> None:
        async with uow:
            app_cover = await uow.app_repo.get_app_cover(cover_id)
            logger.info(f"{app_cover = }")

            if app_cover is None:
                raise app_cover_not_found_exception

            app = await self.get_app(app_cover.app_id)

            if not app.public and app.publisher_id != user_id:
                raise app_not_found_exception

            if app.publisher_id != user_id:
                raise no_rights_exception

            filename = f"{app_cover.id}{app_cover.extension}"
            app_cover_path = settings.APP_COVER_PATH / filename
            os.remove(app_cover_path)

            await uow.session.delete(app_cover)

    async def check_and_remove_all_app_covers(
        self,
        app_id: UUID,
        user_id: UUID,
        uow: UnitOfWork
    ) -> None:
        logger.info("check_and_remove_all_app_covers")
        async with uow:
            app = await uow.app_repo.get_app(app_id)

            if app is None or (not app.public and app.publisher_id != user_id):
                raise app_not_found_exception

            if app.publisher_id != user_id:
                raise no_rights_exception

            await self.remove_all_app_covers(app_id, uow)

    async def remove_all_app_covers(
        self,
        app_id: UUID,
        uow: UnitOfWork
    ) -> None:
        logger.info("remove_all_app_covers")
        app_covers = await uow.app_repo.get_app_covers(app_id)

        for app_cover in app_covers:
            filename = f"{app_cover.id}{app_cover.extension}"
            app_cover_path = settings.APP_COVER_PATH / filename
            os.remove(app_cover_path)
            logger.info(f"Deleting cover at path: {app_cover_path}")
            await uow.session.delete(app_cover)

    async def get_app(self, id: UUID) -> AppDB:
        app = await self.app_repo.get_public_app(id)

        if not app:
            raise app_not_found_exception

        return app

    async def get_apps(
        self, 
        skip: int, 
        limit: Optional[int] = None, 
        search_query: Optional[str] = None
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
        user = await self.user_repo.get_user_by_id(user_id)

        if user is None:
            raise user_not_found_exception

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

    async def get_top_games(
        self, redis: Redis
    ) -> list[AppDB]:
        games = await self.app_repo.get_top_games(0, 10)
        return games

    async def get_top_games_genre(
        self, genre: Optional[GameGenre], redis: Redis
    ) -> list[AppDB]:
        games = await self.app_repo.get_top_games_genre(genre, 0, 10)
        return games

    async def delete_app(
        self, id: UUID, uow: UnitOfWork
    ) -> None:
        app = await uow.app_repo.get_app(id)

        await uow.session.delete(app)
        await self.remove_all_app_covers(id, uow)
        await self.remove_app_archive(id, uow)
        await self.remove_app_thumbnail(id, uow)

    async def delete_app_by_user(
        self, id: UUID, user_id: UUID, uow: UnitOfWork
    ) -> None:
        async with uow:
            app = await uow.app_repo.get_app(id)

            if app is None:
                raise app_not_found_exception
            
            if not app.publisher_id == user_id:
                raise no_rights_exception

            await uow.session.delete(app)
            await self.remove_all_app_covers(id, uow)
            await self.remove_app_archive(id, uow)
            await self.remove_app_thumbnail(id, uow)