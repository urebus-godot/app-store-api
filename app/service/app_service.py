from uuid import UUID
from decimal import Decimal
from typing import Optional
from string import punctuation

from fastapi import UploadFile

from app.core.exceptions import (
    app_not_found_exception, 
    app_not_purchased_exception,
    apps_not_found_exception,
    no_rights_exception
    )
from app.service.user_service import UserService
from app.models.app import AppRequest, AppUpdate, GameGenre, AppDB
from app.models.user import UserDB
from app.repo.app_repo import AppRepository
from app.core.logging import logger


class AppService:
    def __init__(
        self, app_repo: AppRepository, user_service: UserService
    ):
        self.app_repo = app_repo
        self.user_service = user_service

    def format_keywords(self, keywords: list[str]) -> list[str]:
        logger.info(f"Before: {keywords = }")
        new_keywords = []
        for kw in keywords:
            kw = kw.strip()
            kw = kw.lower()
            kw = kw.format_map(
                {c: "" for c in punctuation}
                )
        logger.info(f"After: {keywords = }")
        return new_keywords

    def filter_apps(
        self, 
        apps: list[AppDB], 
        search_query: str
    ) -> list[AppDB]:
        search_keywords = self.format_keywords(search_query.split())
        apps = [
            app for app in apps 
            for kw in search_keywords
            if kw in self.format_keywords(app.keywords)
        ]
        return apps

    def upload_app_file(
        self, file: UploadFile, app_id: UUID
    ):
        if file is not None:
            name, ext = file.filename.split(".")
            filename = app_id + "." + ext
            with open(f"C:/Users/user/Desktop/AppData/{filename}", "wb") as f:
                f.write(file.file.read())

    async def upload_app(
        self, data: AppRequest, user: UserDB, file: UploadFile = None
    ) -> AppDB:
        app = await self.app_repo.upload_app(data, user.id)
        self.upload_app_file(file, app.id)

        return app

    async def download_purchased_app(
        self, id: UUID, user: UserDB
    ):
        app = await self.get_app(id)

        if not app in user.purchased_apps:
            raise app_not_purchased_exception

        return await self.app_repo.download_purchased_app(app)

    async def update_app(
        self, id: UUID, user_id: UUID,
        data: AppUpdate
    ) -> AppDB:
        app = await self.get_app(id, False)

        if app.publisher_id != user_id:
            raise no_rights_exception

        return await self.app_repo.update_app(data, app=app)

    async def get_app(
        self, id: UUID, public_only: bool = True
    ) -> AppDB:
        app = await self.app_repo.get_app(id, public_only)

        if not app:
            raise app_not_found_exception

        return app

    async def get_apps(
        self, 
        skip: int, limit: int,
        search_query: Optional[str] = None
    ) -> list[AppDB]:
        apps = await self.app_repo.get_apps(skip, limit)

        if search_query is not None:
            apps = self.filter_apps(apps, search_query)

        if not apps:
            raise apps_not_found_exception
        
        return apps

    async def get_purchased_apps(
        self, user_id: UUID
    ) -> list[AppDB]:
        purchased_apps = await self.app_repo.get_purchased_apps(user_id)
        return purchased_apps
    
    async def get_publisher_apps(
        self, skip: int, limit: int, 
        user_id: UUID
    ) -> list[AppDB]:
        user = await self.user_service.get_user(id=user_id)
        
        publisher_apps = await self.app_repo.get_publisher_apps(
            skip=skip, limit=limit, user_id=user_id
            )
        
        return publisher_apps

    async def get_games(
        self, 
        skip: int, limit: int,
        search_query: Optional[str] = None, 
        genre: Optional[GameGenre] = None,
        only_public: bool = True
    ) -> list[AppDB]:
        games = await self.app_repo.get_games(genre, skip, limit, only_public)

        if search_query is not None:
            games = self.filter_apps(games, search_query)
        
        return games

    async def delete_app(
        self, id: UUID,
        user_id: UUID
    ) -> None:
        app = await self.get_app(id)

        if not app.publisher_id == user_id:
            raise no_rights_exception
        
        await self.app_repo.delete_app(app)