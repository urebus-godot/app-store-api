from uuid import UUID

from fastapi import APIRouter, status, Depends

from app.api.dependencies import (
    UserIdDep, ReviewServiceDep, rate_limit, SkipLimitParams
    )
from app.schemas.review import ReviewRequest, ReviewResponse

router = APIRouter(
    dependencies=[Depends(rate_limit)]
)


@router.post("/reviews/{app_id}", status_code=status.HTTP_201_CREATED)
async def create_review(
    app_id: UUID,
    data: ReviewRequest,
    user_id: UserIdDep,
    review_service: ReviewServiceDep
) -> ReviewResponse:
    return await review_service.create_review(data, app_id, user_id)


@router.get("/reviews/{app_id}")
async def get_app_reviews(
    skip_limit: SkipLimitParams,
    app_id: UUID, 
    review_service: ReviewServiceDep
) -> list[ReviewResponse]:
    skip, limit = skip_limit
    reviews = await review_service.get_app_reviews(app_id, skip, limit)
    return reviews


@router.get("/users/me/reviews")
async def get_own_reviews(
    skip_limit: SkipLimitParams,
    user_id: UserIdDep, 
    review_service: ReviewServiceDep
) -> list[ReviewResponse]:
    skip, limit = skip_limit
    return await review_service.get_user_reviews(user_id, skip, limit)


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
