from uuid import UUID

from fastapi import APIRouter, status, Depends

from app.api.deps import (
    UserIdDep, ReviewServiceDep, rate_limit, SkipLimitParams
    )
from app.schemas.review import ReviewRequest, ReviewResponse

router = APIRouter(
    dependencies=[Depends(rate_limit)]
)


@router.post(
    "/reviews/{app_id}", 
    status_code=status.HTTP_201_CREATED,
    response_model=ReviewResponse
)
async def create_review(
    app_id: UUID,
    data: ReviewRequest,
    user_id: UserIdDep,
    review_service: ReviewServiceDep
) -> ReviewResponse:
    """Creates a review of the app and adds it to the database.
    
    *Returns*: ReviewResponse object"""
    return await review_service.create_review(data, app_id, user_id)


@router.get(
    "/reviews/{app_id}",
    response_model=list[ReviewResponse]
)
async def get_app_reviews(
    skip_limit: SkipLimitParams,
    app_id: UUID, 
    review_service: ReviewServiceDep
) -> list[ReviewResponse]:
    """Fetches app reviews from the database.
    
    *Returns*: list of ReviewResponse objects"""
    skip, limit = skip_limit
    reviews = await review_service.get_app_reviews(app_id, skip, limit)
    return reviews


@router.get(
    "/users/me/reviews",
    response_model=list[ReviewResponse]
)
async def get_own_reviews(
    skip_limit: SkipLimitParams,
    user_id: UserIdDep, 
    review_service: ReviewServiceDep
) -> list[ReviewResponse]:
    """Fetches the user's reviews from the database.
    
    *Returns*: list of ReviewResponse objects"""
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
    """Deletes the review from the database.
    
    *Returns*: None"""
    await review_service.delete_review(id, user_id)
