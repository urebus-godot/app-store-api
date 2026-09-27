from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.deps import UserIdDep, AppArchiveServiceDep, rate_limit

from app.schemas.file import (
    DownloadPresignResponse,
    AppArchiveUploadPresignRequest,
    UploadPresignResponse,
)

router = APIRouter(
    dependencies=[Depends(rate_limit)]
)


@router.post(
    "/upload_url"
)
async def request_app_archive_upload_url(
    app_id: UUID,
    data: AppArchiveUploadPresignRequest,
    user_id: UserIdDep,
    file_service: AppArchiveServiceDep,
) -> UploadPresignResponse:
    """Запрашивает URL для загрузки архива приложения в MinIO.
    
    **Возвращает**: 
    UploadPresignResponse c URL для загрузки."""
    return await file_service.presign_app_archive_upload(
        app_id=app_id,
        publisher_id=user_id,
        content_type=data.content_type,
        filename=data.filename
    )


@router.post(
    "/confirm", 
    status_code=status.HTTP_204_NO_CONTENT
)
async def confirm_app_archive_upload(
    app_id: UUID,
    user_id: UserIdDep,
    file_service: AppArchiveServiceDep,
) -> None:
    """Подтверждает загрузку архива приложения в MinIO,
    делая ключ объекта (pending_archive_key) действительным.
    
    **Возвращает**: None"""
    await file_service.confirm_app_archive_upload(
        app_id=app_id, publisher_id=user_id
    )


@router.get("/download_url")
async def request_app_archive_download_url(
    app_id: UUID,
    user_id: UserIdDep,
    file_service: AppArchiveServiceDep,
) -> DownloadPresignResponse:
    """Запрашивает URL для скачивания архива приложения в MinIO.
    
    **Возвращает**: 
    DownloadPresignResponse c URL для скачивания."""
    return await file_service.presign_app_archive_download(
        app_id=app_id, user_id=user_id,
    )
