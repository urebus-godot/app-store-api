from uuid import UUID

from fastapi import APIRouter

from app.core.dependencies import SessionDep, UserDep
from app.models.review import ReviewRequest
from app.service import review_service

router = APIRouter(prefix="/api/v1")


@router.post("/reviews/{app_id}")
async def create_review(
    app_id: UUID,
    request: ReviewRequest,
    user: UserDep,
    session: SessionDep
    ):
    return await review_service.create_review(
        app_id, request, user, session
        )


@router.get("/reviews/{app_id}")
async def get_app_reviews(
    app_id: UUID,
    session: SessionDep
    ):
    return await review_service.get_app_reviews(app_id, session)


@router.delete("/reviews/{id}")
async def delete_review(
    id: UUID,
    user: UserDep,
    session: SessionDep
    ):
    return await review_service.delete_review(id, user, session)