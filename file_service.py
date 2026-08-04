import uuid
from pathlib import Path

from fastapi import HTTPException, status

from schemas.storage import DownloadPresignResponse, UploadPresignResponse
from storage.protocols import ObjectStorage
from uow.protocols import UnitOfWork  # твоя существующая абстракция

GAME_BUILDS_BUCKET = "game-builds"
UPLOAD_TTL_SECONDS = 300
DOWNLOAD_TTL_SECONDS = 300


class FileService:
    def __init__(self, storage: ObjectStorage, uow: UnitOfWork) -> None:
        self._storage = storage
        self._uow = uow

    async def presign_game_build_upload(
        self,
        *,
        game_id: uuid.UUID,
        developer_id: uuid.UUID,
        filename: str,
        content_type: str,
    ) -> UploadPresignResponse:
        # Ключ = uuid + расширение, оригинальное имя файла НЕ используем.
        # Так исключаем и коллизии, и path traversal через
        # filename вида "../../etc/passwd" или пробелы/юникод в имени.
        extension = Path(filename).suffix
        object_key = f"{game_id}/{uuid.uuid4()}{extension}"

        async with self._uow:
            game = await self._uow.games.get_owned_by(game_id, developer_id)
            if game is None:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    "Игра не найдена или вам не принадлежит",
                )

            upload_url = await self._storage.generate_presigned_upload_url(
                bucket=GAME_BUILDS_BUCKET,
                key=object_key,
                content_type=content_type,
                expires_in=UPLOAD_TTL_SECONDS,
            )

            # Сохраняем ключ как "pending" ДО того, как клиент реально
            # загрузил файл. Если аплоад оборвётся — останется висячая
            # запись, её можно подчищать periodic Celery-таской.
            game.pending_build_key = object_key
            await self._uow.commit()

        return UploadPresignResponse(
            upload_url=upload_url,
            object_key=object_key,
            expires_in=UPLOAD_TTL_SECONDS,
        )

    async def confirm_game_build_upload(
        self, *, game_id: uuid.UUID, developer_id: uuid.UUID
    ) -> None:
        async with self._uow:
            game = await self._uow.games.get_owned_by(game_id, developer_id)
            if game is None or game.pending_build_key is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Нет ожидающей загрузки")

            # Клиент мог прислать "готово", а сам PUT в MinIO оборваться —
            # поэтому не верим клиенту на слово, а перепроверяем head_object
            exists = await self._storage.object_exists(
                GAME_BUILDS_BUCKET, game.pending_build_key
            )
            if not exists:
                raise HTTPException(status.HTTP_409_CONFLICT, "Файл не найден в хранилище")

            game.build_key = game.pending_build_key
            game.pending_build_key = None
            await self._uow.commit()

    async def presign_game_build_download(
        self, *, game_id: uuid.UUID, user_id: uuid.UUID
    ) -> DownloadPresignResponse:
        async with self._uow:
            has_purchase = await self._uow.purchases.exists(user_id=user_id, game_id=game_id)
            if not has_purchase:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "Игра не куплена")

            game = await self._uow.games.get(game_id)
            if game is None or game.build_key is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Файл игры недоступен")
            build_key = game.build_key

        download_url = await self._storage.generate_presigned_download_url(
            bucket=GAME_BUILDS_BUCKET,
            key=build_key,
            expires_in=DOWNLOAD_TTL_SECONDS,
        )
        return DownloadPresignResponse(download_url=download_url, expires_in=DOWNLOAD_TTL_SECONDS)
