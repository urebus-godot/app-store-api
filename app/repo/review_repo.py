from uuid import UUID
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc

from app.models.review import ReviewRequest, ReviewDB


class ReviewRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_review(
        self, data: ReviewRequest, user_id: UUID, app_id: UUID
    ) -> ReviewDB:
        review = ReviewDB(
            **data.model_dump(), author_id=user_id, app_id=app_id
        )

        self.session.add(review)
        await self.session.commit()
        await self.session.refresh(review)

        return review

    async def get_review(self, id: UUID) -> Optional[ReviewDB]:
        review = (
            await self.session.exec(select(ReviewDB).where(ReviewDB.id == id))
        ).one_or_none()

        return review

    async def get_app_reviews(
        self,
        app_id: UUID,
    ) -> list[ReviewDB]:
        app_reviews = (
            await self.session.exec(
                select(ReviewDB)
                .where(ReviewDB.app_id == app_id)
                .order_by(desc(ReviewDB.created_at))
            )
        ).all()

        return app_reviews

    async def get_user_reviews(self, user_id: UUID) -> list[ReviewDB]:
        user_reviews = await self.session.exec(
            select(ReviewDB)
            .where(ReviewDB.author_id == user_id)
            .order_by(desc(ReviewDB.created_at))
        )
        return user_reviews

    async def delete_review(self, review: ReviewDB) -> None:
        await self.session.delete(review)
