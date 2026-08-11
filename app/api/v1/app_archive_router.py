from app.core.config import settings
import uuid

from fastapi import APIRouter, Depends

from app.api.dependencies import UserIdDep, AppArchiveServiceDep, rate_limit

from app.schemas.storage import (
    DownloadPresignResponse,
    UploadPresignRequest,
    UploadPresignResponse,
)

router = APIRouter(
    dependencies=[Depends(rate_limit)]
)


@router.post(
    "/archive/upload_url", 
    response_model=UploadPresignResponse
)
async def request_app_archive_upload_url(
    app_id: uuid.UUID,
    data: UploadPresignRequest,
    user_id: UserIdDep,
    file_service: AppArchiveServiceDep,
):
    return await file_service.presign_app_archive_upload(
        app_id=app_id,
        publisher_id=user_id,
        filename=data.filename,
        content_type=data.content_type
    )


@router.post("/archive/confirm", status_code=204)
async def confirm_app_archive_upload(
    app_id: uuid.UUID,
    user_id: UserIdDep,
    file_service: AppArchiveServiceDep,
):
    await file_service.confirm_app_archive_upload(
        app_id=app_id, publisher_id=user_id
        )


@router.get("/archive/download_url", response_model=DownloadPresignResponse)
async def request_app_archive_download_url(
    app_id: uuid.UUID,
    user_id: UserIdDep,
    file_service: AppArchiveServiceDep,
):
    return await file_service.presign_app_archive_download(
        app_id=app_id, user_id=user_id,
        )
