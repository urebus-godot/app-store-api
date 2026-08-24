from uuid import UUID

from fastapi import HTTPException, status

from app.core.exceptions import (
    review_not_found_exception, 
    no_rights_exception,
    app_not_purchased_exception,
    app_not_found_exception
    )

from app.schemas.review import ReviewRequest
from app.models.review import ReviewDB

from app.repo.review_repo import ReviewRepository
from app.service.app_service import AppService

from app.uow.orm import UnitOfWork
from app.task_queue.tasks.db_tasks import update_app_rating


class ReviewService:
    def __init__(
        self, 
        review_repo: ReviewRepository, 
        app_service: AppService,
        uow: UnitOfWork
    ):
        self.review_repo = review_repo
        self.app_service = app_service
        self.uow = uow

    async def create_review(
        self, 
        data: ReviewRequest,
        app_id: UUID, 
        user_id: UUID
    ) -> ReviewDB:
        async with self.uow:
            app = await self.uow.app_repo.get_public_app(app_id)
            if not app:
                raise app_not_found_exception

            if app.publisher_id == user_id:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "You can't create review to your own app",
                )
            if await self.uow.review_repo.user_created_review(user_id, app_id):
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    "You already created review to this app",
                )
            if not await self.uow.purchase_repo.user_purchased_app(
                user_id, app_id
            ):
                raise app_not_purchased_exception

            review = await self.uow.review_repo.create_review(
                data, user_id, app_id
            )
            await self.uow.commit()
 
        update_app_rating.delay(str(app_id))
 
        return review

    async def get_review(self, id: UUID) -> ReviewDB:
        review = await self.review_repo.get_review(id)

        if review is None:
            raise review_not_found_exception

        return review

    async def get_app_reviews(
        self,
        app_id: UUID,
        skip: int, limit: int
    ) -> list[ReviewDB]:
        await self.app_service.get_app(app_id)
        app_reviews = await self.review_repo.get_app_reviews(app_id, skip, limit)
        return app_reviews

    async def get_user_reviews(
        self, user_id: UUID, 
        skip: int, limit: int
    ) -> list[ReviewDB]:
        user_reviews = await self.review_repo.get_user_reviews(
            user_id, skip, limit
        )
        return user_reviews

    async def delete_review(
        self, id: UUID, user_id: UUID
    ) -> None:
        async with self.uow:
            review = await self.uow.review_repo.get_review(id)

            if review is None:
                raise review_not_found_exception

            if not review.author_id == user_id:
                raise no_rights_exception

            await self.uow.session.delete(review)
            await self.uow.commit()
            
        app_id = str(review.app_id)
        update_app_rating.delay(app_id)
