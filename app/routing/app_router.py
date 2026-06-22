from typing import Optional
from uuid import UUID

from fastapi import APIRouter

from app.core.dependencies import (
    SessionDep, UserDep, SkipLimitParams, PublisherRoleUser)
from app.core.utils import SearchQuery
from app.models.app import (
    AppRequest, AppUpdate, AppFile, AppResponse, GameGenre)
from app.service import app_service

router = APIRouter(prefix="/api/v1")


@router.post("/apps/upload")
async def upload_app(
    data: AppRequest,
    user: PublisherRoleUser,
    session: SessionDep
) -> AppResponse:
    return await app_service.upload_app(data, user, session)


@router.post("/apps/upload-file")
async def upload_app_file(
    data: AppFile,
    user: PublisherRoleUser,
    session: SessionDep
) -> dict[str, str]:
    return await app_service.upload_app_file(data, user, session)


@router.post("/apps/{id}/add-to-purchases")
async def add_app_to_purchases(
    id: UUID,
    user: UserDep,
    session: SessionDep
) -> dict[str, str]:
    return await app_service.add_app_to_purchases(id, user, session)


@router.get("/apps/purchases/purchase-apps")
async def purchase_apps_in_purchases(
    user: UserDep,
    session: SessionDep
) -> dict[str, str]:
    return await app_service.purchase_apps_in_purchases(
        user, session
        )


@router.patch("/apps/{id}")
async def update_app(
    id: UUID,
    data: AppUpdate,
    session: SessionDep
) -> AppResponse | None:
    return await app_service.update_app(
        data=data, session=session, id=id
        )


@router.get("/apps/{id}/download")
async def download_purchased_app(
    id: UUID,
    user: UserDep,
    session: SessionDep
) -> dict[str, str]:
    return await app_service.download_purchased_app(id, user, session)


@router.get("/apps/by-id/{id}")
async def get_app(
    id: UUID,
    session: SessionDep
) -> AppResponse:
    return await app_service.get_app(id, session)


@router.get("/apps")
async def get_apps(
    skip_limit: SkipLimitParams,
    search_query: SearchQuery,
    session: SessionDep
) -> list[AppResponse]:
    skip, limit = skip_limit
    return await app_service.get_apps(search_query, session, skip, limit)


@router.get("/apps/games")
async def get_games(
    session: SessionDep,
    skip_limit: SkipLimitParams,
    search_query: Optional[SearchQuery] = None,
    genre: Optional[GameGenre] = None,
) -> list[AppResponse]:
    skip, limit = skip_limit
    return await app_service.get_games(
        session=session, search_query=search_query, genre=genre, 
        skip=skip, limit=limit
        )


@router.delete("/apps/{id}")
async def delete_app(
    id: UUID,
    user: UserDep,
    session: SessionDep
) -> dict[str, str]:
    return await app_service.delete_app(id, user, session)