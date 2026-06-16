from fastapi import APIRouter
from app.core.dependencies import SessionDep, UserDep
from app.models.review import ReviewRequest
from app.service import review_service

router = APIRouter(prefix="/api/v1")


@router.post("/reviews/{app_id}")
async def create_review(
    app_id: str,
    request: ReviewRequest,
    user: UserDep,
    session: SessionDep
    ):
    return await review_service.create_review(app_id, session)


@router.get("/reviews/{app_id}")
async def get_app_reviews(
    app_id: str,
    session: SessionDep
    ):
    return await review_service.get_app_reviews(app_id, session)


@router.post("/reviews/{app_id}")
async def create_review(
    app_id: str,
    request: ReviewRequest,
    session: SessionDep
    ):
    return await review_service.create_review()