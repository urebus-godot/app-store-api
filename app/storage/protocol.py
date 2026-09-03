from typing import Protocol


class ObjectStorage(Protocol):
    async def create_bucket(self, name: str, public: bool) -> None:
        ...

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

    async def get_object(self, bucket: str, key: str) -> None:
        ...

    async def object_size(self, bucket: str, key: str) -> int | None:
        ...

    def build_public_url(self, bucket: str, key: str) -> str:
        ...

    async def delete_object(self, bucket: str, key: str) -> None:
        ...

    async def delete_image_variants(
        self, bucket: str, object_key: str
    ) -> None:
        ...