from abc import ABC, abstractmethod

from app.core.logging import logger
from app.repo.purchase_repo import PurchaseRepository
from app.repo.app_repo import AppRepository
from app.repo.review_repo import ReviewRepository
from app.repo.discussion_repo import DiscussionRepository
from app.repo.user_repo import UserRepository
from app.repo.finance_repo import FinanceRepository


class IUnitOfWork(ABC):
    @abstractmethod
    async def __aenter__(self):
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    @abstractmethod
    async def commit(self):
        pass

    @abstractmethod
    async def rollback(self):
        pass


class UnitOfWork(IUnitOfWork):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def __aenter__(self):
        self.session = self.session_factory()

        self.user_repo = UserRepository(self.session)
        self.app_repo = AppRepository(self.session)
        self.review_repo = ReviewRepository(self.session)
        self.discussion_repo = DiscussionRepository(self.session)
        self.purchase_repo = PurchaseRepository(self.session)
        self.finance_repo = FinanceRepository(self.session)

        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            logger.error(
                f"\nType: {exc_type} \nError: {exc_value}"
            )
            await self.rollback()
        else:
            await self.commit()
            
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
