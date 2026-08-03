from typing import Self

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import logger

from app.repo.purchase_repo import PurchaseRepository
from app.repo.app_repo import AppRepository
from app.repo.review_repo import ReviewRepository
from app.repo.discussion_repo import DiscussionRepository
from app.repo.user_repo import UserRepository
from app.repo.finance_repo import FinanceRepository

from app.uow.base import AbstractUnitOfWork

class UnitOfWork(AbstractUnitOfWork):
    def __init__(
        self, 
        session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        self.session_factory = session_factory

    async def __aenter__(self) -> Self:
        self.session = self.session_factory()

        self.user_repo = UserRepository(self.session)
        self.app_repo = AppRepository(self.session)
        self.review_repo = ReviewRepository(self.session)
        self.discussion_repo = DiscussionRepository(self.session)
        self.purchase_repo = PurchaseRepository(self.session)
        self.finance_repo = FinanceRepository(self.session)

        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        if exc_type is not None:
            logger.error(f"Type: {exc_type}")
            logger.error(f"Error: {exc_value}")
            logger.error(f"Traceback: {traceback}")
            await self.rollback()
        #else:
        #    await self.commit()
            
        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()
        logger.debug("Committed current transaction")

    async def rollback(self) -> None:
        await self.session.rollback()
        logger.debug("Rolled transaction back")
