from uuid import UUID
from typing import Optional

from fastapi import HTTPException, status

from app.core.exceptions import (
    app_not_found_exception,
    no_rights_exception,
    user_not_found_exception
)

from app.repo.user_repo import UserRepository

from app.schemas.app import (
    AppRequest, AppUpdate, GameUpdate, 
    )
from app.models.app import GameGenre, AppDB
from app.models.user import UserDB

from app.repo.app_repo import AppRepository
from app.repo.purchase_repo import PurchaseRepository

from app.utils.search import format_keywords

from app.uow.orm import UnitOfWork


class AppService:
    def __init__(
            self, 
            app_repo: AppRepository, 
            user_repo: UserRepository,
            purchase_repo: PurchaseRepository,
            uow: UnitOfWork
            ):
        self.app_repo = app_repo
        self.user_repo = user_repo
        self.purchase_repo = purchase_repo
        self.uow = uow

    async def upload_app(
        self, data: AppRequest, user: UserDB
    ) -> AppDB:
        async with self.uow:
            app = await self.uow.app_repo.upload_app(data, user.id)
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
        if search_query is None:
            apps = await self.app_repo.get_apps(skip, limit)
        else:
            apps = await self.app_repo.get_apps_by_keywords(
                keywords=format_keywords(search_query.split()),
                skip=skip, limit=limit
                )

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
        if search_query is None:
            games = await self.app_repo.get_games(
                genre=genre, 
                skip=skip, limit=limit, 
                only_public=only_public
                )
        else:
            games = await self.app_repo.get_games_by_keywords(
                genre=genre, 
                keywords=format_keywords(search_query.split()), 
                skip=skip, limit=limit
                )

        return games

    async def get_top_games(
        self
    ) -> list[AppDB]:
        games = await self.app_repo.get_top_games(0, 10)
        return games

    async def get_top_games_genre(
        self, genre: Optional[GameGenre]
    ) -> list[AppDB]:
        games = await self.app_repo.get_top_games_genre(genre, 0, 10)
        return games

    async def delete_app(
        self, id: UUID
    ) -> None:
        app = await self.uow.app_repo.get_app(id)

        await self.uow.session.delete(app)

    async def delete_app_by_user(
        self, id: UUID, user_id: UUID
    ) -> None:
        async with self.uow:
            app = await self.uow.app_repo.get_app(id)

            if app is None:
                raise app_not_found_exception
            
            if not app.publisher_id == user_id:
                raise no_rights_exception

            await self.uow.session.delete(app)
            
            await self.uow.commit()
