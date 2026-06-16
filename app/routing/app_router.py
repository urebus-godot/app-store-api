from fastapi import APIRouter
from app.core.dependencies import SessionDep, UserDep
from app.models.app import AppRequest, AppUpdate
from app.service import app_service

router = APIRouter(prefix="/api/v1")


@router.post("/apps")
async def upload_app(
    request: AppRequest,
    session: SessionDep
    ):
    return await app_service.upload_app(request, session)


@router.patch("/apps")
async def update_app(
    update: AppUpdate,
    session: SessionDep
    ):
    return await app_service.update_app(update, session)


@router.get("/apps/{id}")
async def get_app(
    id: str,
    session: SessionDep
    ):
    return await app_service.get_app()


@router.get("/apps")
async def get_apps(
    tags: set[str],
    session: SessionDep
    ):
    return await app_service.get_apps()


@router.delete("/apps")
async def delete_app(
    user: UserDep,
    session: SessionDep
    ):
    return await app_service.delete_app()