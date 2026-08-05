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

    async def delete_object(self, bucket: str, key: str) -> None:
        ...
