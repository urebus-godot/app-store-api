from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models.app_cover import AppCover


class AppCoverRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_cover(self, cover_id: UUID):
        stmt = select(AppCover).where(AppCover.id == cover_id)
        cover = (await self.session.exec(stmt)).one_or_none()
        return cover

    async def get_app_covers(self, app_id: UUID):
        stmt = select(AppCover).where(AppCover.app_id == app_id)
        covers = (await self.session.exec(stmt)).all()
        return covers
