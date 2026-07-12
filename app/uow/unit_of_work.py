from abc import ABC
from collections.abc import AsyncGenerator

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import logger
from app.repo.purchase_repo import PurchaseRepository
from app.repo.app_repo import AppRepository
from app.repo.review_repo import ReviewRepository
from app.repo.discussion_repo import DiscussionRepository
from app.repo.user_repo import UserRepository

from app.db.postgres import get_uow_session


class IUnitOfWork(ABC):
    pass


class UnitOfWork(IUnitOfWork):
    async def __aenter__(self):
        self.session = get_uow_session()

        self.user_repo = UserRepository(self.session)
        self.app_repo = AppRepository(self.session)
        self.review_repo = ReviewRepository(self.session)
        self.discussion_repo = DiscussionRepository(self.session)
        self.purchase_repo = PurchaseRepository(self.session)

        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            logger.error(
        "Error occurred during session transaction! "
        f"\nType: {exc_type} \nError: {exc_value} \nTraceback: {traceback}"
                )
            await self.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()