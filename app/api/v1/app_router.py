from typing import Optional, Annotated
from uuid import UUID
import os

from fastapi import (
    APIRouter, status, 
    Depends, Query,
    UploadFile, File,
    HTTPException, 
    )
from fastapi.responses import FileResponse

from app.dependencies import (
    UserIdDep,
    SkipLimitParams,
    PublisherDep,
    AppServiceDep,
    ReviewServiceDep,
    SessionDep,
    rate_limit,
    UserDep,
    RedisDep,
    UnitOfWorkDep
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
from app.models.file import AppCover, AppArchive
from app.core.logging import logger
from app.core.config import settings

router = APIRouter(
    dependencies=[Depends(rate_limit)]
    )


@router.post(
    "/apps", 
    status_code=status.HTTP_201_CREATED
    )
async def upload_app(
    data: AppRequest,
    user: PublisherDep,
    app_service: AppServiceDep,
    uow: UnitOfWorkDep
) -> AppResponse:
    app = await app_service.upload_app(data, user, uow)
    return app


@router.post(
    "/games", 
    status_code=status.HTTP_201_CREATED
    )
async def upload_game(
    data: GameRequest,
    user: PublisherDep,
    app_service: AppServiceDep,
    uow: UnitOfWorkDep
) -> GameResponse:
    game = await app_service.upload_app(data, user, uow)
    return game


@router.post(
    "/apps/{app_id}/files/archive",
    status_code=status.HTTP_201_CREATED
    )
async def upload_app_archive(
    user_id: UserIdDep,
    app_id: UUID,
    app_service: AppServiceDep,
    uow: UnitOfWorkDep,
    file: UploadFile = File(...)
) -> AppArchive:
    result = await app_service.upload_app_archive(
        uow, file, app_id, user_id
        )
    return result


@router.post(
    "/apps/{app_id}/download"
    )
async def download_app_archive(
    user: UserDep,
    app_id: UUID,
    app_service: AppServiceDep
) -> FileResponse:
    try:
        app_archive = await app_service.get_app_archive(app_id, user)
        filename = f"{app_id}{os.path.splitext(app_archive.filename)[1]}"
        file_path = settings.APP_ARCHIVE_PATH / filename
        return FileResponse(
            path=file_path,
            filename=app_archive.filename
        )
    except FileNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Application has no archive file"
        )


@router.post(
    "/apps/{app_id}/files/thumbnail"
    )
async def upload_app_thumbnail(
    user_id: UserIdDep,
    app_id: UUID,
    uow: UnitOfWorkDep,
    app_service: AppServiceDep,
    file: UploadFile = File(...),
) -> AppCover:
    return NotImplemented


@router.post(
    "/apps/{app_id}/files/covers"
    )
async def upload_app_cover(
    user_id: UserIdDep,
    app_id: UUID,
    uow: UnitOfWorkDep,
    app_service: AppServiceDep,
    file: UploadFile = File(...),
) -> AppCover:
    app_cover = await app_service.upload_app_cover(
        uow, file, app_id, user_id
        )
    return app_cover


@router.get(
    "/apps/{app_id}/files/covers"
    )
async def get_app_covers(
    app_id: UUID,
    app_service: AppServiceDep,
    uow: UnitOfWorkDep
) -> list[AppCover]:
    return await app_service.get_app_covers(app_id, uow)


@router.delete(
    "/apps/{app_id}/files/covers",
    status_code=status.HTTP_204_NO_CONTENT
    )
async def remove_app_cover(
    user_id: UserIdDep,
    cover_id: UUID,
    app_service: AppServiceDep,
    uow: UnitOfWorkDep
) -> None:
    await app_service.remove_app_cover(
        cover_id, user_id, uow
        )


@router.patch(
    "/apps/{id}"
    )
async def update_app(
    id: UUID,
    data: AppUpdate,
    user_id: UserIdDep,
    app_service: AppServiceDep,
    uow: UnitOfWorkDep
) -> AppResponse | GameResponse:
    app = await app_service.update_app(
        data=data, id=id, user_id=user_id, uow=uow
    )
    return get_app_with_rating(app, app.reviews, AppResponse)


@router.get(
    "/apps/{id}"
    )
async def get_app(
    id: UUID, app_service: AppServiceDep
) -> AppResponseWithPublisher | GameResponseWithPublisher:
    logger.info("get_app")
    app = await app_service.get_app(id)
    return get_app_with_rating(app, app.reviews, AppResponseWithPublisher)


@router.get(
    "/apps"
    )
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


@router.get(
    "/games"
    )
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


@router.get(
    "/games/top"
    )
async def get_top_games(
    app_service: AppServiceDep,
    redis: RedisDep,
    genre: Optional[GameGenre] = Query(default=None)
    ) -> list[GameResponseWithPublisher]:
    games = await app_service.get_top_games(genre, redis)
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
    return await get_apps_with_rating(apps, review_service, AppResponse)


@router.get(
    "/apps/published/me"
    )
async def get_own_published_apps(
    user_id: UserIdDep,
    skip_limit: SkipLimitParams,
    review_service: ReviewServiceDep,
    app_service: AppServiceDep,
) -> list[AppResponse | GameResponse]:
    logger.info("get_own_published_apps")
    skip, limit = skip_limit
    apps = await app_service.get_publisher_apps(skip, limit, user_id, False)
    logger.info(f"publshed apps are \n {apps}")
    apps_with_rating = await get_apps_with_rating(
        apps, review_service, AppResponse, False
        )
    logger.info(f"Apps with rating are \n {apps}")
    return apps_with_rating


@router.get(
    "/apps/published/{user_id}"
    )
async def get_publisher_apps(
    user_id: UUID,
    skip_limit: SkipLimitParams,
    app_service: AppServiceDep,
    review_service: ReviewServiceDep,
) -> list[AppResponse | GameResponse]:
    skip, limit = skip_limit
    apps = await app_service.get_publisher_apps(skip, limit, user_id)
    return await get_apps_with_rating(apps, review_service, AppResponse)


@router.delete(
    "/apps/{id}",
    status_code=status.HTTP_204_NO_CONTENT
    )
async def delete_app(
    id: UUID, 
    user_id: UserIdDep, 
    app_service: AppServiceDep,
    uow: UnitOfWorkDep
) -> None:
    return await app_service.delete_app(id, user_id, uow)
