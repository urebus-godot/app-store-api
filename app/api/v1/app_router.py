from typing import Optional
from uuid import UUID

from fastapi import APIRouter, UploadFile

from app.dependencies import (
    UserDep, SkipLimitParams, PublisherDep,
    AppServiceDep)
from app.utils import SearchQuery
from app.models.app import (
    AppRequest, AppUpdate, AppResponse, 
    GameGenre, GameRequest, GameResponse)

router = APIRouter()


@router.post("/apps/upload")
async def upload_app(
    data: AppRequest,
    user: PublisherDep,
    app_service: AppServiceDep
) -> AppResponse:
    return await app_service.upload_app(data, user)


@router.post("/apps/games/upload")
async def upload_game(
    data: GameRequest,
    user: PublisherDep,
    app_service: AppServiceDep
) -> GameResponse:
    return await app_service.upload_app(data, user)


@router.post("/apps/upload-file")
async def upload_app_file(
    data: UploadFile,
    user: PublisherDep,
    app_service: AppServiceDep
) -> dict[str, str]:
    return None#app_service.upload_app_file(data, user)


@router.patch("/apps/{id}")
async def update_app(
    id: UUID,
    data: AppUpdate,
    app_service: AppServiceDep
) -> AppResponse | None:
    return await app_service.update_app(
        data=data, id=id
        )


@router.get("/apps/{id}/download")
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
) -> AppResponse:
    return await app_service.get_app(id)


@router.get("/apps")
async def get_apps(
    skip_limit: SkipLimitParams,
    app_service: AppServiceDep,
    search_query: Optional[SearchQuery] = None,
) -> list[GameResponse]:
    skip, limit = skip_limit
    return await app_service.get_apps(
        search_query, skip, limit
        )


@router.get("/apps/games")
async def get_games(
    skip_limit: SkipLimitParams,
    app_service: AppServiceDep,
    search_query: Optional[SearchQuery] = None,
    genre: Optional[GameGenre] = None,
) -> list[AppResponse]:
    skip, limit = skip_limit
    return await app_service.get_games(
        search_query=search_query, genre=genre, 
        skip=skip, limit=limit
        )


@router.get("/users/me/purchased-apps")
async def get_purchased_apps(
    user: UserDep,
    app_service: AppServiceDep
) -> list[AppResponse]:
    apps = user.purchased_apps
    return apps


@router.get("/users/me/published-apps")
async def get_published_apps(
    user: UserDep,
    app_service: AppServiceDep
) -> list[AppResponse]:
    apps = user.published_apps
    return apps


@router.delete("/apps/{id}")
async def delete_app(
    id: UUID,
    user: PublisherDep,
    app_service: AppServiceDep
) -> dict[str, str]:
    return await app_service.delete_app(id, user)