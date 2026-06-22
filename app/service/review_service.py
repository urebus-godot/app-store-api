from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import APIRouter

from app.core.exceptions import (
    review_not_found_exception, no_rights_exception)
from app.models.review import ReviewRequest, ReviewDB
from app.repo import review_repo
from app.service import app_service


async def create_review(
    app_id: UUID,
    data: ReviewRequest,
    user_id: UUID,
    session: AsyncSession
    ):
    app = await app_service.get_app(id, session)

    return await review_repo.create_review(
        app=app, data=data, user_id=user_id, session=session
        )


async def get_review(
    id: UUID,
    session: AsyncSession
    ):
    review = await review_repo.get_review(id, session)

    if review is None:
        raise review_not_found_exception

    return review


async def get_app_reviews(
    app_id: UUID,
    session: AsyncSession
    ):
    app = await app_service.get_app(id, session) 
    return await review_repo.get_app_reviews(app=app, session=session)


async def delete_review(
    id: UUID,
    user_id: UUID,
    session: AsyncSession
    ):
    review = await get_review(id, session)

    if not review.author_id == user_id:
        raise no_rights_exception
    
    return await review_repo.delete_review(id, session)