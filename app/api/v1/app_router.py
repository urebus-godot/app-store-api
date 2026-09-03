from typing import Optional
from uuid import UUID
import logging

from fastapi import (
    APIRouter, 
    status, 
    Depends, 
    Query,
    BackgroundTasks
)

from app.api.deps import (
    UserIdDep,
    SkipLimitParams,
    PublisherDep,
    AppServiceDep,
    ReviewServiceDep,
    rate_limit
)
from app.utils.search import SearchQuery
from app.base_models.app import (
    GameGenre
)
from app.schemas.app import (
    AppRequest,
    AppUpdate,
    GameUpdate,
    AppResponse,
    GameRequest,
    GameResponse,
    AppResponseWithPublisher,
    GameResponseWithPublisher,
)

router = APIRouter(
    dependencies=[Depends(rate_limit)]
)

logger = logging.getLogger("app.app_router")


@router.post(
    "/apps", 
    status_code=status.HTTP_201_CREATED
    )
async def upload_app(
    data: AppRequest,
    publisher_id: PublisherDep,
    app_service: AppServiceDep
) -> AppResponse:
    app = await app_service.upload_app(data, publisher_id)
    return app


@router.post(
    "/games", 
    status_code=status.HTTP_201_CREATED
    )
async def upload_game(
    data: GameRequest,
    publisher_id: PublisherDep,
    app_service: AppServiceDep
) -> GameResponse:
    game = await app_service.upload_app(data, publisher_id)
    return game


@router.patch(
    "/apps/{id}"
    )
async def update_app(
    id: UUID,
    data: AppUpdate,
    user_id: UserIdDep,
    app_service: AppServiceDep
) -> AppResponse | GameResponse:
    app = await app_service.update_app(
        data=data, id=id, user_id=user_id
    )
    return app


@router.patch(
    "/games/{id}"
    )
async def update_game(
    id: UUID,
    data: GameUpdate,
    user_id: UserIdDep,
    app_service: AppServiceDep
) -> AppResponse | GameResponse:
    app = await app_service.update_app(
        data=data, id=id, user_id=user_id
    )
    return app


@router.get(
    "/apps/{id}"
    )
async def get_app(
    id: UUID, app_service: AppServiceDep
) -> AppResponseWithPublisher | GameResponseWithPublisher:
    logger.info("get_app")
    app = await app_service.get_app(id)
    return app


@router.get(
    "/apps"
    )
async def get_apps(
    skip_limit: SkipLimitParams,
    app_service: AppServiceDep,
    search_query: Optional[SearchQuery] = None,
) -> list[AppResponseWithPublisher]:
    skip, limit = skip_limit
    apps = await app_service.get_apps(
        search_query=search_query, skip=skip, limit=limit
    )
    return apps


@router.get(
    "/games"
    )
async def get_games(
    skip_limit: SkipLimitParams,
    app_service: AppServiceDep,
    search_query: Optional[SearchQuery] = None,
    genre: Optional[GameGenre] = None,
) -> list[GameResponseWithPublisher]:
    skip, limit = skip_limit
    games = await app_service.get_games(
        search_query=search_query, genre=genre, skip=skip, limit=limit
    )
    return games


@router.get(
    "/games/top"
    )
async def get_top_games(
    app_service: AppServiceDep,
    genre: Optional[GameGenre] = Query(default=None)
) -> list[GameResponseWithPublisher]:
    if genre is None:
        games = await app_service.get_top_games()
    else:
        games = await app_service.get_top_games_genre(genre)
    return games


@router.get(
    "/apps/purchased/me"
    )
async def get_purchased_apps(
    user_id: UserIdDep,
    app_service: AppServiceDep,
    review_service: ReviewServiceDep,
) -> list[AppResponse | GameResponse]:
    apps = await app_service.get_purchased_apps(user_id)
    return apps


@router.get(
    "/apps/published/me"
    )
async def get_own_published_apps(
    user_id: UserIdDep,
    skip_limit: SkipLimitParams,
    app_service: AppServiceDep,
) -> list[AppResponse | GameResponse]:
    logger.info("get_own_published_apps")
    skip, limit = skip_limit
    apps = await app_service.get_publisher_apps(
        skip=skip, limit=limit, user_id=user_id, public_only=False
    )
    logger.info(f"published apps are \n {apps}")
    return apps


@router.get(
    "/apps/published/{user_id}"
    )
async def get_publisher_apps(
    user_id: UUID,
    skip_limit: SkipLimitParams,
    app_service: AppServiceDep
) -> list[AppResponse | GameResponse]:
    skip, limit = skip_limit
    apps = await app_service.get_publisher_apps(
        skip=skip, limit=limit, user_id=user_id
    )
    return apps


@router.delete(
    "/apps/{id}",
    status_code=status.HTTP_204_NO_CONTENT
    )
async def delete_app(
    id: UUID, 
    user_id: UserIdDep, 
    app_service: AppServiceDep,
    bg_tasks: BackgroundTasks
) -> None:
    return await app_service.delete_app_by_user(
        id=id, user_id=user_id, bg_tasks=bg_tasks
    )
