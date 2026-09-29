from uuid import UUID

from fastapi import APIRouter, status, Depends

from app.api.deps import (
    UserIdDep, ReviewServiceDep, rate_limit, SkipLimitParams
    )
from app.schemas.review import ReviewRequest, ReviewResponse, ReviewUpdate

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
    """Создаёт отзыв к приложению с указанным *id* в базе данных,
    вызывает фоновую задачу обновления его рейтинга.
    
    **Возвращает**: ReviewResponse"""
    return await review_service.create_review(data, app_id, user_id)


@router.patch(
    "/reviews/{id}",
    response_model=ReviewResponse
)
async def update_review(
    data: ReviewUpdate,
    id: UUID,
    user_id: UserIdDep,
    review_service: ReviewServiceDep
) -> ReviewResponse:
    """Обновляет атрибуты отзыва с указанным *id* в базе данных.
    
    **Возвращает**: ReviewResponse"""
    return await review_service.update_review(
        data=data, review_id=id, user_id=user_id
    )


@router.get(
    "/reviews/{app_id}",
    response_model=list[ReviewResponse]
)
async def get_app_reviews(
    skip_limit: SkipLimitParams,
    app_id: UUID, 
    review_service: ReviewServiceDep
) -> list[ReviewResponse]:
    """Находит отзывы к приложению с указанным *id*.
    
    **Возвращает**: list[ReviewResponse]"""
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
    """Находит отзывы, созданные текущим пользователем.
    
    **Возвращает**: list[ReviewResponse]"""
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
    """Удаляет отзыв с указанным *id*,
    вызывает фоновую задачу обновления рейтинга приложения.
    
    **Возвращает**: None."""
    await review_service.delete_review(id, user_id)
