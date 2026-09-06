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
    "/archive/upload_url"
)
async def request_app_archive_upload_url(
    app_id: UUID,
    data: AppArchiveUploadPresignRequest,
    user_id: UserIdDep,
    file_service: AppArchiveServiceDep,
) -> UploadPresignResponse:
    """Requests URL to upload the app archive file to MinIO storage.
    
    *Returns*: 
    UploadPresignResponse object containing
    upload URL, archive object key, and the expiration time"""
    return await file_service.presign_app_archive_upload(
        app_id=app_id,
        publisher_id=user_id,
        content_type=data.content_type,
        filename=data.filename
    )


@router.post(
    "/archive/confirm", 
    status_code=status.HTTP_204_NO_CONTENT
)
async def confirm_app_archive_upload(
    app_id: UUID,
    user_id: UserIdDep,
    file_service: AppArchiveServiceDep,
) -> None:
    """Confirms that the app archive file has been uploaded to MinIO storage
    and makes it downloadable to users.
    
    *Returns*: None"""
    await file_service.confirm_app_archive_upload(
        app_id=app_id, publisher_id=user_id
    )


@router.get("/archive/download_url")
async def request_app_archive_download_url(
    app_id: UUID,
    user_id: UserIdDep,
    file_service: AppArchiveServiceDep,
) -> DownloadPresignResponse:
    """Requests URL of the app archive file uploaded to MinIO storage.
    
    *Returns*:
    DownloadPresignResponse object containing 
    download URL and the expiration time"""
    return await file_service.presign_app_archive_download(
        app_id=app_id, user_id=user_id,
    )
