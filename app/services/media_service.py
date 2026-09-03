from uuid import UUID, uuid4
import logging

from botocore.exceptions import EndpointConnectionError
from fastapi import HTTPException, status, BackgroundTasks

from app.models.app_cover import AppCover

from app.schemas.media import (
    AppCoverListResponse, 
    AppCoverResponse, 
    MediaConfirmResponse
)
from app.schemas.file import UploadPresignResponse

from app.storage.protocol import ObjectStorage
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

ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

logger = logging.getLogger("services.media")


class MediaService:
    def __init__(
        self, 
        storage: ObjectStorage, 
        uow: UnitOfWork
    ) -> None:
        self.storage = storage
        self.uow = uow

    async def presign_avatar_upload(
        self, user_id: UUID, content_type: str
    ) -> UploadPresignResponse:
        extension = validate_and_get_extension(
            ALLOWED_IMAGE_CONTENT_TYPES, content_type
        )
        object_key = f"users/{user_id}.{extension}"

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
        self, user_id: UUID, bg_tasks: BackgroundTasks
    ) -> MediaConfirmResponse:
        try:
            async with self.uow:
                user = await self.uow.user_repo.get_user_by_id(user_id)

                if user is None:
                    raise user_not_found_exception

                if user.pending_avatar_key is None:
                    raise no_load_exception

                size = await self.storage.object_size(
                    settings.USER_AVATAR_BUCKET, user.pending_avatar_key
                )
                if size is None:
                    raise file_not_found_exception
                
                if to_megabytes(size) > settings.MAX_AVATAR_ICON_SIZE_MB:
                    await self.storage.delete_object(
                        settings.USER_AVATAR_BUCKET, 
                        user.pending_avatar_key
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
                bg_tasks.add_task(
                    self.storage.delete_image_variants, 
                    settings.USER_AVATAR_BUCKET, 
                    old_key
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
                status.HTTP_504_GATEWAY_TIMEOUT,
                "Could not connect to the endpoint URL"
            )

    # ---------- Иконка приложения (одна, заменяемая) ----------

    async def presign_icon_upload(
        self, app_id: UUID, user_id: UUID, content_type: str
    ) -> UploadPresignResponse:
        extension = validate_and_get_extension(
            ALLOWED_IMAGE_CONTENT_TYPES, content_type
            )
        object_key = f"apps/{app_id}/icon.{extension}"

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
        self, app_id: UUID, user_id: UUID, bg_tasks: BackgroundTasks
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
            logger.info(f"Found old key of icon\nOld key: {old_key}")
            bg_tasks.add_task(
                self.storage.delete_image_variants, 
                settings.APP_ICON_BUCKET, 
                old_key
            )

        generate_image_variants.delay(
            settings.APP_ICON_BUCKET, new_key
        )

        return MediaConfirmResponse(
            url=self.storage.build_public_url(
                settings.APP_ICON_BUCKET, new_key
            )
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
        expected_prefix = f"apps/{app_id}/covers/"
        if not object_key.startswith(expected_prefix):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, 
                "Incorrect object_key"
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
                raise file_not_found_exception

            if to_megabytes(size) > settings.MAX_COVER_SIZE_MB:
                await self.storage.delete_object(
                    settings.APP_COVER_BUCKET, object_key
                )
                raise file_too_large_exception

            cover = AppCover(
                app_id=app_id, object_key=object_key
                )
            self.uow.add(cover)
            await self.uow.commit()
            cover_id = cover.id

        generate_image_variants.delay(
            settings.APP_COVER_BUCKET, object_key
        )

        return AppCoverResponse(
            id=cover_id,
            url=self.storage.build_public_url(
                settings.APP_COVER_BUCKET, object_key
            ),
            created_at=cover.created_at
        )

    async def list_covers(
        self, app_id: UUID,
        skip: int, limit: int
    ) -> AppCoverListResponse:
        async with self.uow:
            app = await self.uow.app_repo.get_app(app_id)

            if app is None or not app.public:
                raise app_not_found_exception

            covers = await self.uow.app_cover_repo.get_app_covers(
                app_id, skip, limit
            )

        covers = [
                AppCoverResponse(
                    id=c.id,
                    url=self.storage.build_public_url(
                        settings.APP_COVER_BUCKET, c.object_key
                    ),
                    created_at=c.created_at
                )
                for c in covers
        ]
        return AppCoverListResponse(covers=covers)

    async def delete_cover(
        self, 
        app_id: UUID, user_id: UUID, cover_id: UUID,
        bg_tasks: BackgroundTasks
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
            await self.uow.delete(cover)
            await self.uow.commit()

            bg_tasks.add_task(
                self.storage.delete_image_variants, 
                settings.APP_COVER_BUCKET, 
                object_key
            )

    async def delete_app_covers(
        self, app_id: UUID
    ):
        logger.info(f"delete_app_covers({app_id})")
        app_covers = await self.uow.app_cover_repo.get_all_app_covers(app_id)
        cover_object_keys = [
            cover.object_key for cover 
            in app_covers
        ]
        logger.info(f"{cover_object_keys=}")
        await self.uow.app_cover_repo.delete_app_covers(app_id)

        for object_key in cover_object_keys:
            await self.storage.delete_image_variants(
                settings.APP_COVER_BUCKET, 
                object_key
            )
