import uuid

from fastapi import HTTPException, status

from app.core.exceptions import app_not_purchased_exception
from app.core.config import settings

from app.schemas.storage import DownloadPresignResponse, UploadPresignResponse
from app.storage.protocols import ObjectStorage

from app.uow.base import UnitOfWork
from app.utils.files import validate_and_get_extension

ALLOWED_ARCHIVE_CONTENT_TYPES = {
    "application/zip": "zip",
    "application/x-tar": "tar",
    "application/gzip": "gzip",
    "application/vnd.rar": "rar"
}


class AppArchiveService:
    def __init__(
        self, 
        storage: ObjectStorage, 
        uow: UnitOfWork
    ) -> None:
        self._storage = storage
        self._uow = uow

    async def presign_app_archive_upload(
        self,
        app_id: uuid.UUID,
        publisher_id: uuid.UUID,
        content_type: str
    ) -> UploadPresignResponse:
        # Ключ = uuid + расширение, оригинальное имя файла НЕ используем.
        # Так исключаем и коллизии, и path traversal через
        # filename вида "../../etc/passwd" или пробелы/юникод в имени.
        extension = validate_and_get_extension(
            ALLOWED_ARCHIVE_CONTENT_TYPES, content_type
        )
        object_key = f"{app_id}/{uuid.uuid4()}.{extension}"

        async with self._uow:
            app = await self._uow.app_repo.get_app(app_id)
            
            if app.publisher_id != publisher_id or app is None:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    "Игра не найдена или вам не принадлежит",
                )

            upload_url = await self._storage.generate_presigned_upload_url(
                bucket=settings.APP_ARCHIVE_BUCKET,
                key=object_key,
                content_type=content_type,
                expires_in=settings.UPLOAD_TTL_SECONDS,
            )

            # Сохраняем ключ как "pending" ДО того, как клиент реально
            # загрузил файл. Если аплоад оборвётся — останется висячая
            # запись, её можно подчищать periodic Celery-таской.
            app.pending_archive_key = object_key
            await self._uow.commit()

        return UploadPresignResponse(
            upload_url=upload_url,
            object_key=object_key,
            expires_in=settings.UPLOAD_TTL_SECONDS,
        )

    async def confirm_app_archive_upload(
        self, 
        app_id: uuid.UUID, 
        publisher_id: uuid.UUID
    ) -> None:
        async with self._uow:
            app = await self._uow.app_repo.get_app(app_id)
            if (app.publisher_id != publisher_id 
            or app.pending_archive_key is None):
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND, 
                    "Нет ожидающей загрузки"
                    )

            # Клиент мог прислать "готово", а сам PUT в MinIO оборваться —
            # поэтому не верим клиенту на слово, а перепроверяем head_object
            exists = await self._storage.object_exists(
                settings.APP_ARCHIVE_BUCKET, app.pending_archive_key
            )
            if not exists:
                raise HTTPException(
                    status.HTTP_409_CONFLICT, 
                    "Файл не найден в хранилище"
                    )

            old_key = app.archive_key
            app.archive_key = app.pending_archive_key
            app.pending_archive_key = None
            await self._uow.commit()

            if old_key is not None:
                await self._storage.delete_object(
                    settings.APP_ARCHIVE_BUCKET, old_key
                )

    async def presign_app_archive_download(
        self, app_id: uuid.UUID, user_id: uuid.UUID
    ) -> DownloadPresignResponse:
        async with self._uow:
            app = await self._uow.app_repo.get_app(app_id)

            if app is None or app.archive_key is None:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND, 
                    "Файл игры недоступен"
                    )
            
            if app.publisher_id != user_id:
                has_purchase = await self._uow.purchase_repo.user_purchased_app(
                    user_id=user_id, app_id=app_id
                    )
                if not has_purchase:
                    raise app_not_purchased_exception

            archive_key = app.archive_key

        download_url = await self._storage.generate_presigned_download_url(
            bucket=settings.APP_ARCHIVE_BUCKET,
            key=archive_key,
            expires_in=settings.DOWNLOAD_TTL_SECONDS,
        )
        return DownloadPresignResponse(
            download_url=download_url, 
            expires_in=settings.DOWNLOAD_TTL_SECONDS
            )
