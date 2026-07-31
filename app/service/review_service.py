from uuid import UUID

from fastapi import HTTPException, status

from app.core.logging import logger
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


class ReviewService:
    def __init__(self, review_repo: ReviewRepository, app_service: AppService):
        self.review_repo = review_repo
        self.app_service = app_service

    async def create_review(
        self, 
        data: ReviewRequest,
        app_id: UUID, 
        user_id: UUID, 
        uow: UnitOfWork
    ) -> ReviewDB:
        async with uow:
            app = await uow.app_repo.get_public_app(app_id)
            if not app:
                raise app_not_found_exception
            logger.info(f"{app.publisher_id=} \n{user_id=}")
            if app.publisher_id == user_id:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "You can't create review to your own app",
                )
            if await uow.review_repo.user_created_review(user_id, app_id):
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    "You already created review to this app",
                )
            if not await uow.purchase_repo.user_purchased_app(
                user_id, app_id
            ):
                raise app_not_purchased_exception

            review = await uow.review_repo.create_review(
                data, user_id, app_id
            )

        await self.app_service.update_app_rating(app_id, uow)
        return review

    async def get_review(self, id: UUID) -> ReviewDB:
        review = await self.review_repo.get_review(id)

        if review is None:
            raise review_not_found_exception

        return review

    async def get_app_reviews(
        self,
        app_id: UUID,
        public_only: bool = True
    ) -> list[ReviewDB]:
        await self.app_service.get_app(app_id)
        app_reviews = await self.review_repo.get_app_reviews(app_id)
        return app_reviews

    async def get_user_reviews(self, user_id: UUID) -> list[ReviewDB]:
        user_reviews = await self.review_repo.get_user_reviews(user_id)
        return user_reviews

    async def delete_review(
        self, id: UUID, user_id: UUID, uow: UnitOfWork
    ) -> None:
        async with uow:
            review = await uow.review_repo.get_review(id)

            if review is None:
                raise review_not_found_exception

            if not review.author_id == user_id:
                raise no_rights_exception

            app_id = review.app_id
            
            await uow.session.delete(review)
            await self.app_service.update_app_rating(app_id, uow)
