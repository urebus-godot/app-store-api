from pathlib import Path
from uuid import UUID, uuid4
from typing import Optional
import json
import os

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.exc import InvalidRequestError
from redis.asyncio import Redis

from app.core.logging import logger
from app.core.exceptions import (
    app_not_found_exception,
    no_rights_exception,
    app_not_purchased_exception,
    invalid_file_exception,
    file_too_large_exception,
    app_cover_not_found_exception
)
from app.core.config import settings
from app.service.user_service import UserService
from app.models.app import AppRequest, AppUpdate, GameGenre, AppDB
from app.models.user import UserDB
from app.models.file import AppArchive, AppCover
from app.repo.app_repo import AppRepository

from app.utils.search import filter_apps
from app.utils.files import write_file, to_megabytes

from app.uow.unit_of_work import UnitOfWork


class AppService:
    def __init__(self, app_repo: AppRepository, user_service: UserService):
        self.app_repo = app_repo
        self.user_service = user_service

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
            app = await uow.app_repo.get_app(id, False)

            if app is None:
                raise app_not_found_exception

            if app.publisher_id != user_id:
                raise no_rights_exception

            app = await uow.app_repo.update_app(data, app)

            return app

    async def upload_app_archive(
        self, 
        uow: UnitOfWork, 
        file: UploadFile, 
        app_id: UUID, user_id: UUID
    ) -> AppArchive:
        async with uow:
            app = await self.get_app(app_id, False)
            logger.info(f"Start uploading archive for app: {app_id}")

            if not app.public and app.publisher_id != user_id:
                raise app_not_found_exception

            if app.publisher_id != user_id:
                raise no_rights_exception

            file_size_mb = to_megabytes(file.size)
            if file_size_mb > settings.MAX_APP_ARCHIVE_SIZE_MB:
                raise file_too_large_exception

            extension = os.path.splitext(file.filename)[1]
            logger.info(f"File extension: {extension}")
            
            if extension not in settings.ARCHIVE_EXTENSIONS:
                raise invalid_file_exception

            filename = f"{app_id}{extension}"
            write_file(file, filename, settings.APP_ARCHIVE_PATH)

            app_archive = await uow.app_repo.get_app_archive(app_id)
            
            logger.info(f"{ app_archive = }")

            if app_archive is None:
                app_archive = AppArchive(
                    filename=file.filename, 
                    app_id=app_id
                    )
                uow.session.add(app_archive)
                logger.info(f"Created new app archive")

            app_archive.filename = file.filename

            logger.info(f"Committing. App archive path is now: {settings.APP_ARCHIVE_PATH / str(app_archive.app_id)}")
            return app_archive

    async def get_app_archive(
        self, app_id: UUID, user: UserDB
    ) -> AppArchive:
        app = await self.get_app(app_id)

        if not (app in user.purchased_apps or app.publisher_id == user.id):
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
        try:
            app_archive = await uow.app_repo.get_app_archive(id)
            if app_archive:
                ext = os.path.splitext(app_archive.filename)[1]
                filename = f"{id}{ext}"
                app_archive_path = settings.APP_ARCHIVE_PATH / filename
                os.remove(app_archive_path)
                await uow.session.delete(app_archive)
        except FileNotFoundError:
            logger.error(
                f"Error: FileNotFoundError"
                "Function: remove_app_archive"
                f"File path: {app_archive_path}"
                )

    async def upload_app_cover(
        self,
        uow: UnitOfWork, 
        file: UploadFile, 
        app_id: UUID, user_id: UUID
    ) -> AppCover:
        async with uow:
            app = await self.get_app(app_id, False)
            logger.info(f"Start uploading archive for app: {app_id}")

            if not app.public and app.publisher_id != user_id:
                raise app_not_found_exception

            if app.publisher_id != user_id:
                raise no_rights_exception

            file_size_mb = to_megabytes(file.size)
            if file_size_mb > settings.MAX_IMAGE_SIZE_MB:
                raise file_too_large_exception

            extension = os.path.splitext(file.filename)[1]
            logger.info(f"File extension: {extension}")
            
            if extension not in settings.IMAGE_EXTENSIONS:
                raise invalid_file_exception

            id = uuid4()
            app_cover = AppCover(
                id=id, app_id=app_id, extension=extension
                )
            filename = f"{id}{extension}"
            file_path = write_file(file, filename, settings.APP_COVER_PATH)

            uow.session.add(app_cover)

            logger.info(f"Committed. App cover paths is now: {file_path}")

            return app_cover

    async def get_app_covers(
        self, 
        app_id: UUID,
        uow: UnitOfWork
    ) -> list[AppCover]:
        logger.info(f"\n\n\n {uow.__dict__} \n\n\n")
        app = await self.app_repo.get_app(app_id)

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
        try:
            async with uow:
                app_cover = await uow.app_repo.get_app_cover(cover_id)

                if app_cover is None:
                    raise app_cover_not_found_exception

                app = await self.get_app(app_cover.app_id, False)

                if not app.public and app.publisher_id != user_id:
                    raise app_not_found_exception

                if app.publisher_id != user_id:
                    raise no_rights_exception

                if app_cover is None:
                    raise HTTPException(
                        status.HTTP_404_NOT_FOUND,
                        "App cover not found"
                    )

                filename = f"{app_cover.id}{app_cover.extension}"
                app_cover_path = settings.APP_COVER_PATH / filename
                os.remove(app_cover_path)

                await uow.app_repo.remove_app_cover(app_cover)
        except FileNotFoundError:
            logger.error(
                f"Error: FileNotFoundError"
                "Function: remove_app_archive"
                f"File path: {app_cover_path}"
                )

    async def remove_all_app_covers(
        self,
        app_id: UUID,
        uow: UnitOfWork
    ) -> None:
        try:
            app_covers = await uow.app_repo.get_app_covers(app_id)

            for app_cover in app_covers:
                filename = f"{app_cover.id}{app_cover.extension}"
                app_cover_path = settings.APP_COVER_PATH / filename
                os.remove(app_cover_path)
                await uow.session.delete(app_cover)
        except FileNotFoundError:
            logger.error(
                f"Error: FileNotFoundError"
                "Function: remove_app_archive"
                f"File path: {app_cover_path}"
                )

    async def get_app(self, id: UUID, public_only: bool = True) -> AppDB:
        app = await self.app_repo.get_app(id, public_only)

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

    async def get_top_games(
        self, genre: Optional[GameGenre], redis: Redis
    ) -> list[AppDB]:
        if genre:
            cached_games = await redis.get(f"top_games:{genre}")

            if cached_games:
                logger.info(f"Games from Redis: {cached_games}\nType: {type(cached_games)}")
                if False:
                    return list(AppDB.model_validate_json(game) for game in json.loads(cached_games))

            games = await self.app_repo.get_top_games_genre(genre)
            games_json = [game.model_dump_json() for game in games]

            await redis.set(
                name=f"top_games:{genre}",
                value=json.dumps(games_json),
                ex=settings.CACHE_TTL_SECONDS
                )
        else:
            cached_games = await redis.get("top_games:overall")

            if cached_games:
                logger.info(
                    f"Games from Redis: {cached_games}"
                    f"Type: {type(cached_games)}"
                    )
                if False:
                    return list(AppDB.model_validate_json(game) for game in json.loads(cached_games))

            games = await self.app_repo.get_top_games()
            games_json = [game.model_dump_json() for game in games]

            await redis.set(
                name="top_games:overall",
                value=json.dumps(games_json),
                ex=settings.CACHE_TTL_SECONDS
                )
        logger.info(f"Games from DB: {games}")
        return games

    async def delete_app(
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