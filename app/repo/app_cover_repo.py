from uuid import UUID
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models.app_cover import AppCover


class AppCoverRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_cover(self, cover_id: UUID) -> Optional[AppCover]:
        stmt = select(AppCover).where(AppCover.id == cover_id)
        cover = (await self.session.exec(stmt)).one_or_none()
        return cover

    async def get_app_covers(
        self, app_id: UUID, 
        skip: int, limit: int
    ) -> list[AppCover]:
        stmt = (
            select(AppCover)
            .where(AppCover.app_id == app_id)
            .offset(skip).limit(limit)
            .order_by(AppCover.created_at.desc())
        )
        covers = (await self.session.exec(stmt)).all()
        return covers
