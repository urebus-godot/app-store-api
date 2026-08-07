from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies import UserIdDep, MediaServiceDep
from app.schemas.media import (
    AppCoverListResponse,
    AppCoverResponse,
    ConfirmCoverRequest,
    MediaConfirmResponse,
)
from app.schemas.storage import UploadPresignRequest, UploadPresignResponse

router = APIRouter()


# ---------- Аватар пользователя ----------

@router.post("/users/me/avatar/upload-url", response_model=UploadPresignResponse)
async def request_avatar_upload_url(
    payload: UploadPresignRequest,
    user_id: UserIdDep,
    media_service: MediaServiceDep,
):
    return await media_service.presign_avatar_upload(
        user_id=user_id, content_type=payload.content_type
    )


@router.post("/users/me/avatar/confirm")
async def confirm_avatar_upload(
    user_id: UserIdDep,
    media_service: MediaServiceDep,
) -> MediaConfirmResponse:
    return await media_service.confirm_avatar_upload(user_id=user_id)


# ---------- Иконка приложения ----------

@router.post("/apps/{app_id}/icon/upload-url", response_model=UploadPresignResponse)
async def request_icon_upload_url(
    app_id: UUID,
    payload: UploadPresignRequest,
    user_id: UserIdDep,
    media_service: MediaServiceDep,
):
    return await media_service.presign_icon_upload(
        app_id=app_id, user_id=user_id, content_type=payload.content_type
    )


@router.post("/apps/{app_id}/icon/confirm", response_model=MediaConfirmResponse)
async def confirm_icon_upload(
    app_id: UUID,
    user_id: UserIdDep,
    media_service: MediaServiceDep,
):
    return await media_service.confirm_icon_upload(app_id=app_id, user_id=user_id)


# ---------- Обложки приложения (несколько на одно приложение) ----------

@router.post("/apps/{app_id}/covers/upload-url", response_model=UploadPresignResponse)
async def request_cover_upload_url(
    app_id: UUID,
    payload: UploadPresignRequest,
    user_id: UserIdDep,
    media_service: MediaServiceDep,
):
    return await media_service.presign_cover_upload(
        app_id=app_id, user_id=user_id, content_type=payload.content_type
    )


@router.post("/apps/{app_id}/covers/confirm", response_model=AppCoverResponse)
async def confirm_cover_upload(
    app_id: UUID,
    payload: ConfirmCoverRequest,
    user_id: UserIdDep,
    media_service: MediaServiceDep,
):
    return await media_service.confirm_cover_upload(
        app_id=app_id, user_id=user_id, object_key=payload.object_key
    )


@router.get("/apps/{app_id}/covers", response_model=AppCoverListResponse)
async def list_covers(
    app_id: UUID,
    media_service: MediaServiceDep,
):
    return await media_service.list_covers(app_id=app_id)


@router.delete("/apps/{app_id}/covers/{cover_id}", status_code=204)
async def delete_cover(
    app_id: UUID,
    cover_id: UUID,
    user_id: UserIdDep,
    media_service: MediaServiceDep,
):
    await media_service.delete_cover(app_id=app_id, user_id=user_id, cover_id=cover_id)
