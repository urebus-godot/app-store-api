from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.app import AppRequest, AppUpdate
from app.models.user import UserDB
from app.repo import app_repo

async def app_exists(
        session: AsyncSession,
        app_id: str
        ) -> bool:
    return await app_repo.app_exists(session)


async def upload_app(
        request: AppRequest, session: AsyncSession
        ):
    return await app_repo.upload_app(request, session)


async def update_app(
    update: AppUpdate,
    session: AsyncSession,
    id: str
    ):
    return await app_repo.update_app(update, session)


async def get_app(
    id: str,
    session: AsyncSession
    ):
    return await app_repo.get_app()


async def get_apps(
    tags: set[str],
    session: AsyncSession
    ):
    return await app_repo.get_apps()


async def delete_app(
    user: UserDB,
    session: AsyncSession
    ):
    return await app_repo.delete_app()