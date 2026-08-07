from typing import Protocol


class ObjectStorage(Protocol):
    """Абстракция над файловым хранилищем.

    Сервис зависит от этого интерфейса, а не от aioboto3/MinIO напрямую.
    В тестах можно подставить FakeObjectStorage (dict в памяти) вместо
    поднятия настоящего MinIO контейнера.
    """

    async def generate_presigned_upload_url(
        self,
        bucket: str,
        key: str,
        content_type: str,
        expires_in: int = 300,
    ) -> str:
        ...

    async def generate_presigned_download_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 300,
    ) -> str:
        ...

    async def object_exists(self, bucket: str, key: str) -> bool:
        ...

    async def object_size(self, bucket: str, key: str) -> int | None:
        """Размер объекта в байтах или None, если объекта нет.

        Используется для валидации лимита на файл ПОСЛЕ загрузки — сам
        presigned PUT (в отличие от presigned POST с policy) размер
        не ограничивает, так что проверять приходится постфактум.
        """
        ...

    def build_public_url(self, bucket: str, key: str) -> str:
        """URL для чтения объекта из публично доступного бакета.

        Без подписи — используется только для бакетов с bucket policy
        "public read" (avatars, app-icons, app-covers), а не для
        приватных game-builds.
        """
        ...

    async def delete_object(self, bucket: str, key: str) -> None:
        ...
