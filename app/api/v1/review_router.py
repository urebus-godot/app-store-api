from uuid import UUID

from fastapi import APIRouter, status

from app.dependencies import UserIdDep, ReviewServiceDep, UnitOfWorkDep
from app.models.review import ReviewRequest, ReviewResponse

router = APIRouter()


@router.post("/reviews/{app_id}", status_code=status.HTTP_201_CREATED)
async def create_review(
    app_id: UUID,
    data: ReviewRequest,
    user_id: UserIdDep,
    review_service: ReviewServiceDep
) -> ReviewResponse:
    return await review_service.create_review(app_id, data, user_id)


@router.get("/reviews/{app_id}")
async def get_app_reviews(
    app_id: UUID, review_service: ReviewServiceDep
) -> list[ReviewResponse]:
    reviews = await review_service.get_app_reviews(app_id)
    return reviews


@router.get("/users/me/reviews")
async def get_own_reviews(
    user_id: UserIdDep, review_service: ReviewServiceDep
) -> list[ReviewResponse]:
    return await review_service.get_user_reviews(user_id)


@router.delete(
    "/reviews/{id}", 
    status_code=status.HTTP_204_NO_CONTENT
    )
async def delete_review(
    id: UUID,
    user_id: UserIdDep,
    review_service: ReviewServiceDep
) -> None:
    await review_service.delete_review(id, user_id)
