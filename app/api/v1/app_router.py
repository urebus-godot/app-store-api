from typing import Optional
from uuid import UUID

from fastapi import APIRouter, status

from app.dependencies import (
    UserIdDep,
    SkipLimitParams,
    PublisherDep,
    AppServiceDep,
    ReviewServiceDep,
    UnitOfWorkDep,
)
from app.utils.app import get_apps_with_rating, get_app_with_rating
from app.utils.search import SearchQuery
from app.models.app import (
    AppRequest,
    AppUpdate,
    AppResponse,
    GameGenre,
    GameRequest,
    GameResponse,
    AppResponseWithPublisher,
    GameResponseWithPublisher,
)
from app.core.logging import logger

router = APIRouter()


@router.post("/apps", status_code=status.HTTP_201_CREATED)
async def upload_app(
    data: AppRequest,
    user: PublisherDep,
    app_service: AppServiceDep,
    uow: UnitOfWorkDep,
) -> AppResponse:
    app = await app_service.upload_app(data, user, uow)
    return app


@router.post("/games", status_code=status.HTTP_201_CREATED)
async def upload_game(
    data: GameRequest,
    user: PublisherDep,
    app_service: AppServiceDep,
    uow: UnitOfWorkDep,
) -> GameResponse:
    game = await app_service.upload_app(data, user, uow)
    return game


@router.patch("/apps/{id}")
async def update_app(
    id: UUID,
    data: AppUpdate,
    user_id: UserIdDep,
    app_service: AppServiceDep,
    uow: UnitOfWorkDep,
) -> Optional[AppResponse]:
    app = await app_service.update_app(
        data=data, id=id, user_id=user_id, uow=uow
    )
    return get_app_with_rating(app, app.reviews, AppResponse)


@router.get("/apps/{id}")
async def get_app(
    id: UUID, app_service: AppServiceDep
) -> AppResponseWithPublisher:
    app = await app_service.get_app(id)
    return get_app_with_rating(app, app.reviews, AppResponseWithPublisher)


@router.get("/apps")
async def get_apps(
    skip_limit: SkipLimitParams,
    app_service: AppServiceDep,
    review_service: ReviewServiceDep,
    search_query: Optional[SearchQuery] = None,
) -> list[AppResponseWithPublisher]:
    skip, limit = skip_limit
    apps = await app_service.get_apps(
        search_query=search_query, skip=skip, limit=limit
    )
    return await get_apps_with_rating(
        apps, review_service, AppResponseWithPublisher
    )


@router.get("/games")
async def get_games(
    skip_limit: SkipLimitParams,
    app_service: AppServiceDep,
    review_service: ReviewServiceDep,
    search_query: Optional[SearchQuery] = None,
    genre: Optional[GameGenre] = None,
) -> list[GameResponseWithPublisher]:
    skip, limit = skip_limit
    games = await app_service.get_games(
        search_query=search_query, genre=genre, skip=skip, limit=limit
    )
    return await get_apps_with_rating(
        games, review_service, GameResponseWithPublisher
    )


@router.get("/apps/purchased/me")
async def get_purchased_apps(
    user_id: UserIdDep,
    app_service: AppServiceDep,
    review_service: ReviewServiceDep,
) -> list[AppResponse]:
    apps = await app_service.get_purchased_apps(user_id)
    return await get_apps_with_rating(apps, review_service, AppResponse)


@router.get("/apps/published/me")
async def get_own_published_apps(
    user_id: UserIdDep,
    skip_limit: SkipLimitParams,
    review_service: ReviewServiceDep,
    app_service: AppServiceDep,
) -> list[AppResponse]:
    skip, limit = skip_limit
    apps = await app_service.get_publisher_apps(skip, limit, user_id)
    logger.info(f"publshed apps are \n {apps}")
    return await get_apps_with_rating(apps, review_service, AppResponse)


@router.get("/apps/published/{user_id}")
async def get_publisher_apps(
    user_id: UUID,
    skip_limit: SkipLimitParams,
    app_service: AppServiceDep,
    review_service: ReviewServiceDep,
) -> list[AppResponse]:
    skip, limit = skip_limit
    apps = await app_service.get_publisher_apps(skip, limit, user_id)
    return await get_apps_with_rating(apps, review_service, AppResponse)


@router.delete("/apps/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_app(
    id: UUID, user: UserIdDep, app_service: AppServiceDep, uow: UnitOfWorkDep
) -> None:
    return await app_service.delete_app(id, user, uow)
