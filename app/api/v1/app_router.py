from typing import Optional
from uuid import UUID

from fastapi import APIRouter, UploadFile

from app.dependencies import (
    UserDep, UserIdDep, SkipLimitParams, PublisherDep,
    AppServiceDep, ReviewServiceDep
    )
from app.utils import SearchQuery, get_apps_with_rating, get_app_with_rating
from app.models.app import (
    AppRequest, AppUpdate, AppResponse,
    GameGenre, GameRequest, GameResponse,
    AppResponseWithPublisher
    )
from app.core.logging import logger

router = APIRouter()


@router.post("/apps/upload")
async def upload_app(
    data: AppRequest,
    user: PublisherDep,
    app_service: AppServiceDep
) -> AppResponse:
    app = await app_service.upload_app(data, user)
    return app


@router.post("/apps/games/upload")
async def upload_game(
    data: GameRequest,
    user: PublisherDep,
    app_service: AppServiceDep
) -> GameResponse:
    game = await app_service.upload_app(data, user)
    return game


@router.post("/apps/upload-file")
async def upload_app_file(
    data: UploadFile,
    user: PublisherDep,
    app_service: AppServiceDep
):
    return None#app_service.upload_app_file(data, user)


@router.patch("/apps/{id}")
async def update_app(
    id: UUID,
    data: AppUpdate,
    app_service: AppServiceDep
) -> Optional[AppResponse]:
    app = await app_service.update_app(
        data=data, id=id
        )
    return app


@router.get("/apps/by-id/{id}/download")
async def download_purchased_app(
    id: UUID,
    user: UserDep,
    app_service: AppServiceDep
) -> dict[str, str]:
    return await app_service.download_purchased_app(id, user)


@router.get("/apps/by-id/{id}")
async def get_app(
    id: UUID,
    app_service: AppServiceDep
) -> AppResponseWithPublisher:
    app = await app_service.get_app(id)
    return get_app_with_rating(
        app, app.reviews, "AppResponseWithPublisher"
        )


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
    return await get_apps_with_rating(apps, review_service)


@router.get("/apps/games")
async def get_games(
    skip_limit: SkipLimitParams,
    app_service: AppServiceDep,
    review_service: ReviewServiceDep,
    search_query: Optional[SearchQuery] = None,
    genre: Optional[GameGenre] = None,
) -> list[AppResponseWithPublisher]:
    skip, limit = skip_limit
    games = await app_service.get_games(
        search_query, genre, skip, limit
        ) 
    return await get_apps_with_rating(games, review_service)


@router.get("/users/me/purchased-apps")
async def get_purchased_apps(
    user_id: UserIdDep,
    app_service: AppServiceDep,
    review_service: ReviewServiceDep,
) -> list[AppResponse]:
    apps = await app_service.get_purchased_apps(user_id)
    return await get_apps_with_rating(apps, review_service)


@router.get("/users/me/published-apps")
async def get_own_published_apps(
    user_id: UserIdDep,
    skip_limit: SkipLimitParams,
    review_service: ReviewServiceDep,
    app_service: AppServiceDep
) -> list[AppResponse]:
    skip, limit = skip_limit
    apps = await app_service.get_publisher_apps(skip, limit, user_id)
    logger.info(f"publshed apps are \n {apps}")
    return await get_apps_with_rating(apps, review_service)


@router.get("/users/by-id/{user_id}/published-apps")
async def get_publisher_apps(
    user_id: UUID,
    skip_limit: SkipLimitParams,
    app_service: AppServiceDep,
    review_service: ReviewServiceDep
) -> list[AppResponse]:
    skip, limit = skip_limit
    apps = await app_service.get_publisher_apps(
        skip, limit, user_id
        )
    return await get_apps_with_rating(apps, review_service)


@router.delete("/apps/by-id/{id}")
async def delete_app(
    id: UUID,
    user: PublisherDep,
    app_service: AppServiceDep
) -> dict[str, str]:
    return await app_service.delete_app(id, user)