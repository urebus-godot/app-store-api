from uuid import UUID
from typing import Optional


from app.uow.unit_of_work import UnitOfWork
from app.core.exceptions import (
    app_not_found_exception,
    no_rights_exception,
)
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
        self, data: AppRequest, user: UserDB, uow: UnitOfWork
    ) -> AppDB:
        async with uow:
            app = await self.app_repo.upload_app(data, user.id)
            await uow.commit()
            return app

    async def update_app(
        self, id: UUID, user_id: UUID, data: AppUpdate, uow: UnitOfWork
    ) -> AppDB:
        async with uow:
            app = await self.get_app(id, False)

            if app.publisher_id != user_id:
                raise no_rights_exception

            app = await self.app_repo.update_app(data, app=app)

            await uow.commit()

            return app

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
        self, skip: int, limit: int, user_id: UUID
    ) -> list[AppDB]:
        await self.user_service.get_user(id=user_id)

        publisher_apps = await self.app_repo.get_publisher_apps(
            skip=skip, limit=limit, user_id=user_id
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

    async def delete_app(
        self, id: UUID, user_id: UUID, uow: UnitOfWork
    ) -> None:
        async with uow:
            app = await self.get_app(id)

            if not app.publisher_id == user_id:
                raise no_rights_exception

            await self.app_repo.delete_app(app)
            await uow.commit()
