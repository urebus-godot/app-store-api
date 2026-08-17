from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import UserIdDep, MediaServiceDep, rate_limit

from app.schemas.media import (
    AppCoverListResponse,
    AppCoverResponse,
    ConfirmCoverRequest,
    MediaConfirmResponse,
)
from app.schemas.file import UploadPresignRequest, UploadPresignResponse

router = APIRouter(
    dependencies=[Depends(rate_limit)]
)


@router.post(
    "/users/me/avatar/upload-url"
)
async def request_avatar_upload_url(
    payload: UploadPresignRequest,
    user_id: UserIdDep,
    media_service: MediaServiceDep,
) -> UploadPresignResponse:
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

@router.post(
    "/apps/{app_id}/icon/upload-url"
)
async def request_icon_upload_url(
    app_id: UUID,
    payload: UploadPresignRequest,
    user_id: UserIdDep,
    media_service: MediaServiceDep,
) -> UploadPresignResponse:
    return await media_service.presign_icon_upload(
        app_id=app_id, user_id=user_id, content_type=payload.content_type
    )


@router.post(
    "/apps/{app_id}/icon/confirm"
)
async def confirm_icon_upload(
    app_id: UUID,
    user_id: UserIdDep,
    media_service: MediaServiceDep,
) -> MediaConfirmResponse:
    return await media_service.confirm_icon_upload(
        app_id=app_id, user_id=user_id
    )


@router.post(
    "/apps/{app_id}/covers/upload-url",
)
async def request_cover_upload_url(
    app_id: UUID,
    payload: UploadPresignRequest,
    user_id: UserIdDep,
    media_service: MediaServiceDep,
) -> UploadPresignResponse:
    return await media_service.presign_cover_upload(
        app_id=app_id, user_id=user_id, content_type=payload.content_type
    )


@router.post(
    "/apps/{app_id}/covers/confirm",
)
async def confirm_cover_upload(
    app_id: UUID,
    payload: ConfirmCoverRequest,
    user_id: UserIdDep,
    media_service: MediaServiceDep,
) -> AppCoverResponse:
    return await media_service.confirm_cover_upload(
        app_id=app_id, user_id=user_id, object_key=payload.object_key
    )


@router.get(
    "/apps/{app_id}/covers"
)
async def list_covers(
    app_id: UUID,
    media_service: MediaServiceDep,
) -> AppCoverListResponse:
    return await media_service.list_covers(app_id=app_id)


@router.delete(
    "/apps/{app_id}/covers/{cover_id}", 
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_cover(
    app_id: UUID,
    cover_id: UUID,
    user_id: UserIdDep,
    media_service: MediaServiceDep,
) -> None:
    await media_service.delete_cover(
        app_id=app_id, user_id=user_id, cover_id=cover_id
    )
