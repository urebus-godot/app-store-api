import os
from uuid import UUID
from decimal import Decimal
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions import (
    app_not_found_exception, 
    not_enough_funds_exception,
    app_not_purchased_exception,
    apps_not_found_exception,
    no_rights_exception)
from app.core.utils import filter_apps
from app.models.app import AppRequest, AppUpdate, GameGenre, AppDB, AppFile
from app.models.user import UserDB
from app.repo import app_repo

async def upload_app(
    data: AppRequest, user: UserDB, session: AsyncSession
) -> AppDB:
    return await app_repo.upload_app(data, user.id, session)


async def upload_app_file(
        data: AppFile, user: UserDB, session: AsyncSession
):
    with open(f"app_files/{data.filename}") as file:
        file.write(data.file.file)
    return {"message": "File has been uploaded"}


async def add_app_to_purchases(
    id: UUID, user: UserDB, session: AsyncSession
):
    app = await get_app(id, session)

    return await app_repo.add_app_to_purchases(
        user=user, app=app, session=session
        )


async def purchase_apps_in_purchases(
    user: UserDB, session: AsyncSession
):
    total_cost = Decimal(0)

    for app in user.apps_to_purchase:
        total_cost += app.price

    if user.balance < total_cost:
        raise not_enough_funds_exception

    return await app_repo.purchase_apps_in_purchases(
        user, total_cost, session
        )


async def download_purchased_app(
    id: UUID, user: UserDB, session: AsyncSession
):
    app = await get_app(id, session)

    if not id in user.purchased_app_ids:
        raise app_not_purchased_exception

    return await app_repo.download_purchased_app(id, session)


async def update_app(
    id: UUID,
    data: AppUpdate,
    session: AsyncSession,
):
    app = await get_app(id, session)

    return await app_repo.update_app(data, session, app=app)


async def get_app(
    id: UUID,
    session: AsyncSession
):
    app = await app_repo.get_app(id, session)

    if not app or not app.public:
        raise app_not_found_exception

    return app


async def get_apps(
    search_query: str,
    session: AsyncSession,
    skip: int, limit: int
):
    apps = await app_repo.get_apps(session, skip, limit)
    apps = filter_apps(apps, search_query)

    if apps:
        return apps
    raise apps_not_found_exception


async def get_games(
    search_query: Optional[str], 
    genre: Optional[GameGenre],
    skip: int,
    limit: int,
    session: AsyncSession
) -> list[AppDB]:
    games = await app_repo.get_games(genre, session, skip, limit)
    games = filter_apps(games, search_query)

    if games:
        return games
    raise apps_not_found_exception


async def delete_app(
    id: UUID,
    user: UserDB,
    session: AsyncSession
) -> dict[str, str]:
    app = await get_app(id, session)

    if not app.publisher_id == user.id:
        raise no_rights_exception
    
    return await app_repo.delete_app(session=session, app=app)