from uuid import UUID
from typing import Optional
from abc import ABC, abstractmethod

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.repo.app_repo import AppRepository
from app.models.review import ReviewRequest, ReviewDB
from app.models.app import AppDB


class AbstractReviewRepository(ABC):
    @abstractmethod
    async def create_review(
        self, data: ReviewRequest,
        user_id: UUID,
        app_id: Optional[UUID] = None,
        app: Optional[AppDB] = None
    ) -> ReviewDB:
        pass

    @abstractmethod
    async def get_review(
        self, id: UUID
    ) -> ReviewDB | None:
        pass

    @abstractmethod
    async def get_app_reviews(
        self, app_id: UUID,
    ) -> list[ReviewDB]:
        pass

    @abstractmethod
    async def get_user_reviews(self, user_id: UUID) -> list[ReviewDB]:
        pass

    @abstractmethod
    async def delete_review(
        self,   
        id: Optional[UUID] = None,
        review: Optional[ReviewDB] = None
    ) -> dict[str, str]:
        pass


class ReviewRepository(AbstractReviewRepository):
    def __init__(
        self, session: AsyncSession, app_repo: AppRepository
    ):
        self.session = session
        self.app_repo = app_repo
            
    async def create_review(
        self, data: ReviewRequest,
        user_id: UUID,
        app_id: Optional[UUID] = None,
        app: Optional[AppDB] = None
    ) -> ReviewDB:
        if app is None:
            app = await self.app_repo.get_app(app_id)

        review = ReviewDB(
            **data.model_dump(),
            author_id=user_id,
            app_id=app.id
            )

        self.session.add(review)
        await self.session.commit()
        await self.session.refresh(review)

        return review

    async def get_review(
        self, id: UUID
    ) -> ReviewDB | None:
        review = (await self.session.exec(
            select(ReviewDB).where(ReviewDB.id == id)
        )).one_or_none()

        return review

    async def get_app_reviews(
        self,
        app_id: UUID,
    ) -> list[ReviewDB]:
        app_reviews = (await self.session.exec(
            select(ReviewDB).where(ReviewDB.app_id == app_id)
        )).all()

        return app_reviews

    async def get_user_reviews(self, user_id: UUID) -> list[ReviewDB]:
        user_reviews = await self.session.exec(
            select(ReviewDB).where(ReviewDB.author_id == user_id)
        )
        return user_reviews

    async def delete_review(
        self,   
        id: Optional[UUID] = None,
        review: Optional[ReviewDB] = None
    ) -> dict[str, str]:
        if review is None:
            review = await self.get_review(id)

        await self.session.delete(review)
        await self.session.commit()
        #await session.flush(review)

        return {"message": "Review has been deleted"}