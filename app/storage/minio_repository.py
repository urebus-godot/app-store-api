import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings

class MinioStorage:
    def __init__(self) -> None:
        self._session = aioboto3.Session()
        common = dict(
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(
                signature_version="s3v4", 
                s3={'addressing_style': 'path'}
                ),
            region_name="us-east-1",
        )
        self._internal_kwargs = {
            **common, "endpoint_url": settings.MINIO_INTERNAL_ENDPOINT
            }
        self._public_kwargs = {
            **common, "endpoint_url": settings.MINIO_PUBLIC_ENDPOINT
            }

    async def generate_presigned_upload_url(
        self,
        bucket: str,
        key: str,
        content_type: str,
        expires_in: int = 300,
    ) -> str:
        async with self._session.client("s3", **self._public_kwargs) as client:
            return await client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": bucket, 
                    "Key": key, 
                    "ContentType": content_type
                    },
                ExpiresIn=expires_in,
            )

    async def generate_presigned_download_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 300,
    ) -> str:
        async with self._session.client("s3", **self._public_kwargs) as client:
            return await client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in,
            )

    async def object_exists(self, bucket: str, key: str) -> bool:
        return await self.object_size(bucket, key) is not None

    async def object_size(self, bucket: str, key: str) -> int | None:
        async with self._session.client(
            "s3", **self._internal_kwargs
        ) as client:
            try:
                response = await client.head_object(Bucket=bucket, Key=key)
                return response["ContentLength"]
            except ClientError as e:
                if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
                    return None
                raise

    def build_public_url(self, bucket: str, key: str) -> str:
        return f"{settings.MINIO_PUBLIC_ENDPOINT}/{bucket}/{key}"

    async def delete_object(self, bucket: str, key: str) -> None:
        async with self._session.client(
            "s3", **self._internal_kwargs
        ) as client:
            await client.delete_object(Bucket=bucket, Key=key)