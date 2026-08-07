from uuid import UUID, uuid4

from botocore.exceptions import EndpointConnectionError
from fastapi import HTTPException, status

from app.models.app_cover import AppCover

from app.schemas.media import AppCoverListResponse, AppCoverResponse, MediaConfirmResponse
from app.schemas.storage import UploadPresignResponse

from app.storage.protocols import ObjectStorage

from app.uow.base import UnitOfWork
from app.core.exceptions import (
    user_not_found_exception, 
    app_not_found_exception, 
    no_rights_exception,
    app_cover_not_found_exception,
    file_too_large_exception,
    file_not_found_exception,
    no_load_exception
    )
from app.core.config import settings
from app.core.logging import logger
from app.utils.files import validate_and_get_extension

# Ключ = content_type -> расширение. Заодно это единственный источник
# правды о том, какие типы файлов вообще разрешены к загрузке.
ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


class MediaService:
    def __init__(self, storage: ObjectStorage, uow: UnitOfWork) -> None:
        self._storage = storage
        self._uow = uow

    # ---------- Аватар пользователя (один, заменяемый) ----------

    async def presign_avatar_upload(
        self, *, user_id: UUID, content_type: str
    ) -> UploadPresignResponse:
        extension = validate_and_get_extension(
            ALLOWED_IMAGE_CONTENT_TYPES, content_type
            )
        object_key = f"users/{user_id}/{uuid4()}.{extension}"

        async with self._uow:
            user = await self._uow.user_repo.get_user_by_id(user_id)
            if user is None:
                raise user_not_found_exception

            upload_url = await self._storage.generate_presigned_upload_url(
                bucket=settings.USER_AVATAR_BUCKET,
                key=object_key,
                content_type=content_type,
                expires_in=settings.UPLOAD_TTL_SECONDS,
            )
            user.pending_avatar_key = object_key
            await self._uow.commit()

        return UploadPresignResponse(
            upload_url=upload_url, object_key=object_key, expires_in=settings.UPLOAD_TTL_SECONDS
        )

    async def confirm_avatar_upload(self, *, user_id: UUID) -> MediaConfirmResponse:
        try:
            async with self._uow:
                user = await self._uow.user_repo.get_user_by_id(user_id)
                if user is None or user.pending_avatar_key is None:
                    raise no_load_exception

                size = await self._storage.object_size(settings.USER_AVATAR_BUCKET, user.pending_avatar_key)
                if size is None:
                    raise file_not_found_exception
                if size > settings.MAX_AVATAR_ICON_SIZE:
                    await self._storage.delete_object(settings.USER_AVATAR_BUCKET, user.pending_avatar_key)
                    user.pending_avatar_key = None
                    await self._uow.commit()
                    raise file_too_large_exception

                old_key = user.avatar_key
                logger.info(f"{old_key = }")
                user.avatar_key = user.pending_avatar_key
                user.pending_avatar_key = None
                await self._uow.commit()
                new_key = user.avatar_key
                logger.info(f"{new_key = }")

            if old_key:
                await self._storage.delete_object(settings.USER_AVATAR_BUCKET, old_key)
                logger.info(f"Deleting {old_key = }...")

            return MediaConfirmResponse(url=self._storage.build_public_url(settings.USER_AVATAR_BUCKET, new_key))
        except EndpointConnectionError:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Could not connect to the endpoint URL"
            )

    # ---------- Иконка приложения (одна, заменяемая) ----------

    async def presign_icon_upload(
        self, *, app_id: UUID, user_id: UUID, content_type: str
    ) -> UploadPresignResponse:
        extension = validate_and_get_extension(
            ALLOWED_IMAGE_CONTENT_TYPES, content_type
            )
        object_key = f"apps/{app_id}/icon/{uuid4()}.{extension}"

        async with self._uow:
            app = await self._uow.app_repo.get_app(app_id)
            
            if app is None:
                raise app_not_found_exception

            if app.publisher_id != user_id:
                raise no_rights_exception

            upload_url = await self._storage.generate_presigned_upload_url(
                bucket=settings.APP_ICON_BUCKET,
                key=object_key,
                content_type=content_type,
                expires_in=settings.UPLOAD_TTL_SECONDS,
            )
            app.pending_icon_key = object_key
            await self._uow.commit()

        return UploadPresignResponse(
            upload_url=upload_url, object_key=object_key, expires_in=settings.UPLOAD_TTL_SECONDS
        )

    async def confirm_icon_upload(
        self, *, app_id: UUID, user_id: UUID
    ) -> MediaConfirmResponse:
        async with self._uow:
            app = await self._uow.app_repo.get_app(app_id)
            if app is None or app.pending_icon_key is None:
                raise no_load_exception

            size = await self._storage.object_size(settings.APP_ICON_BUCKET, app.pending_icon_key)
            if size is None:
                raise file_not_found_exception
            
            if size > settings.MAX_AVATAR_ICON_SIZE:
                await self._storage.delete_object(settings.APP_ICON_BUCKET, app.pending_icon_key)
                app.pending_icon_key = None
                await self._uow.commit()
                raise file_too_large_exception

            old_key = app.icon_key
            app.icon_key = app.pending_icon_key
            app.pending_icon_key = None
            await self._uow.commit()
            new_key = app.icon_key

        if old_key:
            await self._storage.delete_object(settings.APP_ICON_BUCKET, old_key)

        return MediaConfirmResponse(url=self._storage.build_public_url(settings.APP_ICON_BUCKET, new_key))

    # ---------- Обложки приложения (МНОГО на одно приложение) ----------

    async def presign_cover_upload(
        self, *, app_id: UUID, user_id: UUID, content_type: str
    ) -> UploadPresignResponse:
        extension = validate_and_get_extension(
            ALLOWED_IMAGE_CONTENT_TYPES, content_type
            )
        object_key = f"apps/{app_id}/covers/{uuid4()}.{extension}"

        async with self._uow:
            app = await self._uow.app_repo.get_app(app_id)
            if app is None:
                raise app_not_found_exception

            if app.publisher_id != user_id:
                raise no_rights_exception

            upload_url = await self._storage.generate_presigned_upload_url(
                bucket=settings.APP_COVER_BUCKET,
                key=object_key,
                content_type=content_type,
                expires_in=settings.UPLOAD_TTL_SECONDS,
            )
        # Важное отличие от аватара/иконки: у app НЕТ pending_cover_key —
        # обложек может грузиться несколько параллельно, единственное
        # pending-поле для этого не подходит. Запись в БД появляется
        # только в confirm. "Осиротевший" файл без записи в БД просто
        # безвредно лежит в бакете — вычищается периодической Celery-таской.
        return UploadPresignResponse(
            upload_url=upload_url, object_key=object_key, expires_in=settings.UPLOAD_TTL_SECONDS
        )

    async def confirm_cover_upload(
        self, *, app_id: UUID, user_id: UUID, object_key: str
    ) -> AppCoverResponse:
        # object_key пришёл в теле запроса от клиента — нельзя доверять ему
        # вслепую, иначе можно подсунуть чужой ключ и "привязать" его к
        # своему приложению
        expected_prefix = f"apps/{app_id}/covers/"
        if not object_key.startswith(expected_prefix):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Некорректный object_key")

        async with self._uow:
            app = await self._uow.app_repo.get_app(app_id)
            if app is None:
                raise app_not_found_exception

            if app.publisher_id != user_id:
                raise no_rights_exception

            size = await self._storage.object_size(settings.APP_COVER_BUCKET, object_key)
            if size is None:
                raise HTTPException(status.HTTP_409_CONFLICT, "Файл не найден в хранилище")
            if size > settings.MAX_COVER_SIZE:
                await self._storage.delete_object(settings.APP_COVER_BUCKET, object_key)
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Файл больше 10 МБ")

            #position = await self._uow.app_cover_repo.next_position(app_id)
            cover = AppCover(app_id=app_id, object_key=object_key, position=0)
            self._uow.session.add(cover)
            await self._uow.commit()
            cover_id = cover.id

        return AppCoverResponse(
            id=cover_id,
            url=self._storage.build_public_url(settings.APP_COVER_BUCKET, object_key),
            position=0,
        )

    async def list_covers(self, *, app_id: UUID) -> AppCoverListResponse:
        async with self._uow:
            covers = await self._uow.app_cover_repo.get_app_covers(app_id)

        return AppCoverListResponse(
            covers=[
                AppCoverResponse(
                    id=c.id,
                    url=self._storage.build_public_url(settings.APP_COVER_BUCKET, c.object_key),
                    position=c.position,
                )
                for c in covers
            ]
        )

    async def delete_cover(
        self, *, app_id: UUID, user_id: UUID, cover_id: UUID
    ) -> None:
        async with self._uow:
            app = await self._uow.app_repo.get_app(app_id)
            if app is None:
                raise app_not_found_exception

            if app.publisher_id != user_id:
                raise no_rights_exception

            cover = await self._uow.app_cover_repo.get_cover(cover_id)
            if cover is None or cover.app_id != app_id:
                raise app_cover_not_found_exception

            object_key = cover.object_key
            await self._uow.session.delete(cover)
            await self._uow.commit()

        await self._storage.delete_object(settings.APP_COVER_BUCKET, object_key)
"""
curl -X PUT \
  -H "Content-Type: application/zip" \
  --data-binary "@/mnt/c/Users/user/Downloads/типы.zip" \
  "http://localhost:9000/app-archives/413709c7-316b-4f62-93dd-a77477dbc892/79d9de9b-ecbf-413e-8a5e-973b6630edec.zip?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=user%2F20260807%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260807T104142Z&X-Amz-Expires=600&X-Amz-SignedHeaders=content-type%3Bhost&X-Amz-Signature=2cc128baf4b5d6434f2728863d2ff338b07fba07c62e7244f4cf0703faff5c24"
  """

"""
curl -X GET \
  -H "Content-Type: image/png" \
  "http://localhost:9000/app-icons/apps/413709c7-316b-4f62-93dd-a77477dbc892/icon/743db3ee-8c12-4dbe-9281-6407afc2fffd.png"
  """
