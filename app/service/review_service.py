from uuid import UUID

from app.core.exceptions import (
    review_not_found_exception, no_rights_exception)
from app.models.review import ReviewRequest, ReviewDB
from app.models.user import UserDB
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
    ):
        app = await self.app_service.get_app(app_id)

        return await self.review_repo.create_review(
            app=app, data=data, user_id=user_id
            )

    async def get_review(
        self, id: UUID
    ):
        review = await self.review_repo.get_review(id)

        if review is None:
            raise review_not_found_exception

        return review

    async def get_app_reviews(
        self, app_id: UUID
    ):
        app = await self.app_service.get_app(app_id) 
        return await self.review_repo.get_app_reviews(app=app)

    async def get_user_reviews(
        self, user: UserDB
    ):
        return user.reviews
        

    async def delete_review(
        self, id: UUID,
        user_id: UUID
    ):
        review = await self.get_review(id)

        if not review.author_id == user_id:
            raise no_rights_exception
        
        return await self.review_repo.delete_review(id)