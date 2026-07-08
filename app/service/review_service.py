from uuid import UUID

from fastapi import HTTPException, status

from app.core.logging import logger
from app.core.exceptions import (
    review_not_found_exception, 
    no_rights_exception
    )
from app.models.review import ReviewRequest
from app.models.review import ReviewDB
from app.repo.review_repo import ReviewRepository
from app.service.app_service import AppService


class ReviewService:
    def __init__(
        self, review_repo: ReviewRepository, app_service: AppService
    ):
        self.review_repo = review_repo
        self.app_service = app_service

    async def create_review(
        self, app_id: UUID,
        data: ReviewRequest,
        user_id: UUID
    ) -> ReviewDB:
        app = await self.app_service.get_app(app_id)
        logger.info(f"{app.publisher_id=} \n{user_id=}")
        if app.publisher_id == user_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "You can't create review to your own app"
            )

        return await self.review_repo.create_review(
            app=app, data=data, user_id=user_id
            )

    async def get_review(
        self, id: UUID
    ) -> ReviewDB:
        review = await self.review_repo.get_review(id)

        if review is None:
            raise review_not_found_exception

        return review

    async def get_app_reviews(
        self, app_id: UUID,
    ) -> list[ReviewDB]:
        app_reviews = await self.review_repo.get_app_reviews(app_id)
        return app_reviews

    async def get_user_reviews(
        self, user_id: UUID
    ) -> list[ReviewDB]:
        user_reviews = await self.review_repo.get_user_reviews(user_id)
        return user_reviews

    async def delete_review(
        self, id: UUID,
        user_id: UUID
    ) -> None:
        review = await self.get_review(id)

        if not review.author_id == user_id:
            raise no_rights_exception
        
        await self.review_repo.delete_review(review)