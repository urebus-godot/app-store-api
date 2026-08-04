import uuid

from fastapi import APIRouter, Depends

from api.dependencies import get_current_user_id, get_file_service
from schemas.storage import (
    DownloadPresignResponse,
    UploadPresignRequest,
    UploadPresignResponse,
)
from services.file_service import FileService

router = APIRouter(prefix="/games/{game_id}/build", tags=["files"])


@router.post("/upload-url", response_model=UploadPresignResponse)
async def request_upload_url(
    game_id: uuid.UUID,
    payload: UploadPresignRequest,
    developer_id: uuid.UUID = Depends(get_current_user_id),
    file_service: FileService = Depends(get_file_service),
):
    return await file_service.presign_game_build_upload(
        game_id=game_id,
        developer_id=developer_id,
        filename=payload.filename,
        content_type=payload.content_type,
    )


@router.post("/confirm", status_code=204)
async def confirm_upload(
    game_id: uuid.UUID,
    developer_id: uuid.UUID = Depends(get_current_user_id),
    file_service: FileService = Depends(get_file_service),
):
    await file_service.confirm_game_build_upload(game_id=game_id, developer_id=developer_id)


@router.get("/download-url", response_model=DownloadPresignResponse)
async def request_download_url(
    game_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    file_service: FileService = Depends(get_file_service),
):
    return await file_service.presign_game_build_download(game_id=game_id, user_id=user_id)
