from uuid import UUID
from typing import Optional
import logging

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, delete

from app.models.app_cover import AppCoverDB

logger = logging.getLogger("repo.app_cover")


class AppCoverRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_cover(self, cover_id: UUID) -> Optional[AppCoverDB]:
        stmt = select(AppCoverDB).where(AppCoverDB.id == cover_id)
        cover = (await self.session.exec(stmt)).one_or_none()
        return cover

    async def get_app_covers(
        self, app_id: UUID, 
        skip: int = 0, 
        limit: int = 10
    ) -> list[AppCoverDB]:
        stmt = (
            select(AppCoverDB)
            .where(AppCoverDB.app_id == app_id)
            .offset(skip).limit(limit)
            .order_by(AppCoverDB.created_at.desc())
        )
            
        covers = (await self.session.exec(stmt)).all()
        logger.info(f"App covers: {covers}")
        return covers

    async def get_all_app_covers(
        self, app_id: UUID
    ) -> list[AppCoverDB]:
        stmt = (
            select(AppCoverDB)
            .where(AppCoverDB.app_id == app_id)
        )

        covers = (await self.session.exec(stmt)).all()
        logger.info(f"App covers: {covers}")
        return covers

    async def delete_app_covers(
        self, app_id: UUID
    ) -> None:
        stmt = (
            delete(AppCoverDB)
            .where(AppCoverDB.app_id == app_id)
        )
        await self.session.exec(stmt)
