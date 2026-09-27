from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.deps import (
    UserIdDep, MediaServiceDep, rate_limit, SkipLimitParams
)

from app.schemas.media import (
    AppCoverResponse,
    ConfirmCoverRequest,
    MediaConfirmResponse,
)
from app.schemas.file import UploadPresignRequest, UploadPresignResponse

router = APIRouter(
    dependencies=[Depends(rate_limit)]
)


@router.post(
    "/users/me/avatar/upload_url"
)
async def request_avatar_upload_url(
    payload: UploadPresignRequest,
    user_id: UserIdDep,
    media_service: MediaServiceDep,
) -> UploadPresignResponse:
    """Запрашивает URL для загрузки аватара пользователя в MinIO.
    
    **Возвращает**: 
    UploadPresignResponse c URL для загрузки."""
    return await media_service.presign_avatar_upload(
        user_id=user_id, content_type=payload.content_type
    )


@router.post(
    "/users/me/avatar/confirm",
    status_code=status.HTTP_201_CREATED
)
async def confirm_avatar_upload(
    user_id: UserIdDep,
    media_service: MediaServiceDep,
) -> MediaConfirmResponse:
    """Подтверждает загрузку аватара пользователя в MinIO,
    делая ключ объекта (pending_avatar_key) действительным.
    
    **Возвращает**: MediaConfirmResponse с URL для скачивания файлы."""
    return await media_service.confirm_avatar_upload(
        user_id=user_id
        
    )


@router.post(
    "/apps/{app_id}/icon/upload_url"
)
async def request_icon_upload_url(
    app_id: UUID,
    payload: UploadPresignRequest,
    user_id: UserIdDep,
    media_service: MediaServiceDep,
) -> UploadPresignResponse:
    """Запрашивает URL для загрузки иконки приложения в MinIO.
    
    **Возвращает**: 
    UploadPresignResponse c URL для загрузки."""
    return await media_service.presign_icon_upload(
        app_id=app_id, user_id=user_id, content_type=payload.content_type
    )


@router.post(
    "/apps/{app_id}/icon/confirm",
    status_code=status.HTTP_201_CREATED
)
async def confirm_icon_upload(
    app_id: UUID,
    user_id: UserIdDep,
    media_service: MediaServiceDep
) -> MediaConfirmResponse:
    """Подтверждает загрузку иконки приложения в MinIO,
    делая ключ объекта иконки (pending_icon_key) действительным.
    
    **Возвращает**: MediaConfirmResponse с URL для скачивания файлы."""
    return await media_service.confirm_icon_upload(
        app_id=app_id, user_id=user_id
    )


@router.post(
    "/apps/{app_id}/covers/upload_url",
)
async def request_cover_upload_url(
    app_id: UUID,
    payload: UploadPresignRequest,
    user_id: UserIdDep,
    media_service: MediaServiceDep,
) -> UploadPresignResponse:
    """Запрашивает URL для загрузки обложки приложения в MinIO.
    
    **Возвращает**: 
    UploadPresignResponse c URL для загрузки."""
    return await media_service.presign_cover_upload(
        app_id=app_id, user_id=user_id, content_type=payload.content_type
    )


@router.post(
    "/apps/{app_id}/covers/confirm",
    status_code=status.HTTP_201_CREATED
)
async def confirm_cover_upload(
    app_id: UUID,
    payload: ConfirmCoverRequest,
    user_id: UserIdDep,
    media_service: MediaServiceDep,
) -> AppCoverResponse:
    """Подтверждает загрузку иконки приложения в MinIO и
    создаёт обложку (AppCover) в базе данных.
    
    **Возвращает**: AppCoverResponse."""
    return await media_service.confirm_cover_upload(
        app_id=app_id, user_id=user_id, object_key=payload.object_key
    )


@router.get(
    "/apps/{app_id}/covers"
)
async def get_app_covers(
    skip_limit: SkipLimitParams,
    app_id: UUID,
    user_id: UserIdDep,
    media_service: MediaServiceDep,
) -> list[AppCoverResponse]:
    """Находит обложки приложения с указанным *id* в базе данных.
    
    **Возвращает**: list[AppCoverResponse]."""
    skip, limit = skip_limit
    return await media_service.get_app_covers(
        app_id=app_id, user_id=user_id,
        skip=skip, limit=limit
    )


@router.delete(
    "/apps/{app_id}/covers/{cover_id}", 
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_cover(
    app_id: UUID,
    cover_id: UUID,
    user_id: UserIdDep,
    media_service: MediaServiceDep
) -> None:
    """Удаляет обложку приложения с указанным *id* из базы данных.
    
    **Возвращает**: None."""
    await media_service.delete_cover(
        app_id=app_id, 
        user_id=user_id, 
        cover_id=cover_id
    )
