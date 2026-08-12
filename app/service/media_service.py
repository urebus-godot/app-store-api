from uuid import UUID, uuid4
import logging

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
from app.utils.files import validate_and_get_extension, to_megabytes

from app.task_queue.tasks.media_tasks import generate_image_variants

# Ключ = content_type -> расширение. Заодно это единственный источник
# правды о том, какие типы файлов вообще разрешены к загрузке.
ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

logger = logging.getLogger("media_service")


class MediaService:
    def __init__(self, storage: ObjectStorage, uow: UnitOfWork) -> None:
        self.storage = storage
        self.uow = uow

    async def presign_avatar_upload(
        self, user_id: UUID, content_type: str
    ) -> UploadPresignResponse:
        extension = validate_and_get_extension(
            ALLOWED_IMAGE_CONTENT_TYPES, content_type
            )
        object_key = f"users/{user_id}/{uuid4()}.{extension}"

        async with self.uow:
            user = await self.uow.user_repo.get_user_by_id(user_id)
            if user is None:
                raise user_not_found_exception

            upload_url = await self.storage.generate_presigned_upload_url(
                bucket=settings.USER_AVATAR_BUCKET,
                key=object_key,
                content_type=content_type,
                expires_in=settings.UPLOAD_TTL_SECONDS,
            )
            user.pending_avatar_key = object_key
            await self.uow.commit()

        return UploadPresignResponse(
            upload_url=upload_url, 
            object_key=object_key, 
            expires_in=settings.UPLOAD_TTL_SECONDS
        )

    async def confirm_avatar_upload(
        self, user_id: UUID
    ) -> MediaConfirmResponse:
        try:
            async with self.uow:
                user = await self.uow.user_repo.get_user_by_id(user_id)
                if user is None or user.pending_avatar_key is None:
                    raise no_load_exception

                size = await self.storage.object_size(
                    settings.USER_AVATAR_BUCKET, user.pending_avatar_key
                )
                if size is None:
                    raise file_not_found_exception
                if to_megabytes(size) > settings.MAX_AVATAR_ICON_SIZE_MB:
                    await self.storage.delete_object(
                        settings.USER_AVATAR_BUCKET, user.pending_avatar_key
                    )
                    user.pending_avatar_key = None
                    await self.uow.commit()
                    raise file_too_large_exception

                old_key = user.avatar_key
                logger.info(f"{old_key = }")
                user.avatar_key = user.pending_avatar_key
                user.pending_avatar_key = None
                await self.uow.commit()
                new_key = user.avatar_key
                logger.info(f"{new_key = }")

            if old_key:
                await self.storage.delete_object(
                    settings.USER_AVATAR_BUCKET, old_key
                )
                logger.info(f"Deleting {old_key = }...")

            generate_image_variants.delay(
                settings.USER_AVATAR_BUCKET, new_key
            )

            return MediaConfirmResponse(url=self.storage.build_public_url(
                settings.USER_AVATAR_BUCKET, new_key
                )
            )
        except EndpointConnectionError:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Could not connect to the endpoint URL"
            )

    # ---------- Иконка приложения (одна, заменяемая) ----------

    async def presign_icon_upload(
        self, app_id: UUID, user_id: UUID, content_type: str
    ) -> UploadPresignResponse:
        extension = validate_and_get_extension(
            ALLOWED_IMAGE_CONTENT_TYPES, content_type
            )
        object_key = f"apps/{app_id}/icon/{uuid4()}.{extension}"

        async with self.uow:
            app = await self.uow.app_repo.get_app(app_id)
            
            if app is None:
                raise app_not_found_exception

            if app.publisher_id != user_id:
                raise no_rights_exception

            upload_url = await self.storage.generate_presigned_upload_url(
                bucket=settings.APP_ICON_BUCKET,
                key=object_key,
                content_type=content_type,
                expires_in=settings.UPLOAD_TTL_SECONDS,
            )
            app.pending_icon_key = object_key
            await self.uow.commit()

        return UploadPresignResponse(
            upload_url=upload_url, 
            object_key=object_key, 
            expires_in=settings.UPLOAD_TTL_SECONDS
        )

    async def confirm_icon_upload(
        self, app_id: UUID, user_id: UUID
    ) -> MediaConfirmResponse:
        async with self.uow:
            app = await self.uow.app_repo.get_app(app_id)

            if app is None or app.pending_icon_key is None:
                raise no_load_exception

            if app.publisher_id != user_id:
                raise no_rights_exception

            size = await self.storage.object_size(
                settings.APP_ICON_BUCKET, app.pending_icon_key
            )
            if size is None:
                raise file_not_found_exception
            
            if to_megabytes(size) > settings.MAX_AVATAR_ICON_SIZE_MB:
                await self.storage.delete_object(
                    settings.APP_ICON_BUCKET, app.pending_icon_key
                )
                app.pending_icon_key = None
                await self.uow.commit()
                raise file_too_large_exception

            old_key = app.icon_key
            app.icon_key = app.pending_icon_key
            app.pending_icon_key = None
            await self.uow.commit()
            new_key = app.icon_key

        if old_key:
            await self.storage.delete_object(
                settings.APP_ICON_BUCKET, old_key
            )

        generate_image_variants.delay(
            settings.APP_ICON_BUCKET, new_key
        )

        return MediaConfirmResponse(
            url=self.storage.build_public_url(settings.APP_ICON_BUCKET, new_key)
            )

    # ---------- Обложки приложения (МНОГО на одно приложение) ----------

    async def presign_cover_upload(
        self, app_id: UUID, user_id: UUID, content_type: str
    ) -> UploadPresignResponse:
        extension = validate_and_get_extension(
            ALLOWED_IMAGE_CONTENT_TYPES, content_type
            )
        object_key = f"apps/{app_id}/covers/{uuid4()}.{extension}"

        async with self.uow:
            app = await self.uow.app_repo.get_app(app_id)
            if app is None:
                raise app_not_found_exception

            if app.publisher_id != user_id:
                raise no_rights_exception

            upload_url = await self.storage.generate_presigned_upload_url(
                bucket=settings.APP_COVER_BUCKET,
                key=object_key,
                content_type=content_type,
                expires_in=settings.UPLOAD_TTL_SECONDS,
            )

        return UploadPresignResponse(
            upload_url=upload_url, 
            object_key=object_key, 
            expires_in=settings.UPLOAD_TTL_SECONDS
        )

    async def confirm_cover_upload(
        self, app_id: UUID, user_id: UUID, object_key: str
    ) -> AppCoverResponse:
        # object_key пришёл в теле запроса от клиента — нельзя доверять ему
        # вслепую, иначе можно подсунуть чужой ключ и "привязать" его к
        # своему приложению
        expected_prefix = f"apps/{app_id}/covers/"
        if not object_key.startswith(expected_prefix):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, 
                "Некорректный object_key"
            )

        async with self.uow:
            app = await self.uow.app_repo.get_app(app_id)
            if app is None:
                raise app_not_found_exception

            if app.publisher_id != user_id:
                raise no_rights_exception

            size = await self.storage.object_size(
                settings.APP_COVER_BUCKET, object_key
            )
            if size is None:
                raise HTTPException(
                    status.HTTP_409_CONFLICT, 
                    "Файл не найден в хранилище"
                )
            if to_megabytes(size) > settings.MAX_COVER_SIZE_MB:
                await self.storage.delete_object(
                    settings.APP_COVER_BUCKET, object_key
                )
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, 
                    "Файл больше 10 МБ"
                )

            cover = AppCover(
                app_id=app_id, object_key=object_key
                )
            self.uow.session.add(cover)
            await self.uow.commit()
            cover_id = cover.id

        generate_image_variants.delay(
            settings.APP_COVER_BUCKET, object_key
        )

        return AppCoverResponse(
            id=cover_id,
            url=self.storage.build_public_url(
                settings.APP_COVER_BUCKET, object_key
            )
        )

    async def list_covers(self, app_id: UUID) -> AppCoverListResponse:
        async with self.uow:
            covers = await self.uow.app_cover_repo.get_app_covers(app_id)

        return AppCoverListResponse(
            covers=[
                AppCoverResponse(
                    id=c.id,
                    url=self.storage.build_public_url(
                        settings.APP_COVER_BUCKET, c.object_key
                    ),
                    position=c.position,
                )
                for c in covers
            ]
        )

    async def delete_cover(
        self, app_id: UUID, user_id: UUID, cover_id: UUID
    ) -> None:
        async with self.uow:
            app = await self.uow.app_repo.get_app(app_id)
            if app is None:
                raise app_not_found_exception

            if app.publisher_id != user_id:
                raise no_rights_exception

            cover = await self.uow.app_cover_repo.get_cover(cover_id)
            if cover is None or cover.app_id != app_id:
                raise app_cover_not_found_exception

            object_key = cover.object_key
            await self.uow.session.delete(cover)
            await self.uow.commit()

        await self.storage.delete_object(
            settings.APP_COVER_BUCKET, object_key
        )
"""
curl -X PUT \
  -H "Content-Type: image/png" \
  --data-binary "@/mnt/c/Users/user/Downloads/GetImage.PNG" \
  "http://localhost:9000/user-avatars/users/e5c34317-172c-43ff-ba26-ec394348a3cc/fe9af225-7fc3-4b40-ace9-674fbd314d64.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=user%2F20260812%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260812T103412Z&X-Amz-Expires=600&X-Amz-SignedHeaders=content-type%3Bhost&X-Amz-Signature=581fcf01358d33c68c5f971c5622cf7f96ff36d0a1c87623614c8e1826e037e4"
  """

"""
curl -X GET \
  "http://localhost:9001/api/v1/buckets/user-avatars/objects/download?prefix=users%2Fe5c34317-172c-43ff-ba26-ec394348a3cc%2Ffe9af225-7fc3-4b40-ace9-674fbd314d64.png&version_id=null"
"""
