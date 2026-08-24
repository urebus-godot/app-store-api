from uuid import UUID
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models.review import ReviewDB
from app.schemas.review import ReviewRequest


class ReviewRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def user_created_review(
        self, user_id: UUID, app_id: UUID
    ) -> bool:
        stmt = select(ReviewDB).where(
            ReviewDB.author_id == user_id,
            ReviewDB.app_id == app_id
        )
        review = (await self.session.exec(stmt)).one_or_none()
        return review is not None

    async def create_review(
        self, data: ReviewRequest, user_id: UUID, app_id: UUID
    ) -> ReviewDB:
        review = ReviewDB(
            **data.model_dump(), 
            author_id=user_id, 
            app_id=app_id
        )

        self.session.add(review)

        return review

    async def get_review(
        self, id: UUID
    ) -> Optional[ReviewDB]:
        review = (
            await self.session.exec(select(ReviewDB).where(ReviewDB.id == id))
        ).one_or_none()

        return review

    async def get_app_reviews(
        self,
        app_id: UUID,
        skip: int, limit: int
    ) -> list[ReviewDB]:
        app_reviews = (
            await self.session.exec(
                select(ReviewDB)
                .where(ReviewDB.app_id == app_id)
                .offset(skip)
                .limit(limit)
                .order_by(ReviewDB.created_at.desc())
            )
        ).all()

        return app_reviews

    async def get_user_reviews(
        self, user_id: UUID, 
        skip: int, limit: int
    ) -> list[ReviewDB]:
        user_reviews = await self.session.exec(
            select(ReviewDB)
            .where(ReviewDB.author_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(ReviewDB.created_at.desc())
        )
        return user_reviews
