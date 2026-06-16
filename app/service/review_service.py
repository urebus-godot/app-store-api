from fastapi import APIRouter
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.review import ReviewRequest
from app.repo import review_repo

async def create_review(
    app_id: str,
    request: ReviewRequest,
    session: AsyncSession
    ):
    return await review_repo.create_review(app_id, session)


async def get_app_reviews(
    app_id: str,
    session: AsyncSession
    ):
    return await review_repo.get_app_reviews(app_id, session)


async def delete_review(
    app_id: str,
    request: ReviewRequest,
    session: AsyncSession
    ):
    return await review_repo.create_review()