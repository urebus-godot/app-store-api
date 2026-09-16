import json
import logging

import aioboto3
from botocore.exceptions import ClientError

from app.core.config import settings

from app.utils.files import variant_key

logger = logging.getLogger("storage.minio_repo")


class MinioStorage:
    def __init__(
        self, 
        options: dict
    ) -> None:
        self._session = aioboto3.Session()
        internal_endpoint = options.pop(
            "internal_endpoint", settings.MINIO_INTERNAL_ENDPOINT)
        public_endpoint = options.pop(
                    "public_endpoint", settings.MINIO_PUBLIC_ENDPOINT)
        self._internal_kwargs = {
            **options, "endpoint_url": internal_endpoint
        }
        self._public_kwargs = {
            **options, "endpoint_url":  public_endpoint
        }
        logger.info(f"{self._internal_kwargs}\n\n{self._public_kwargs}")

    async def create_bucket(self, bucket_name: str, public: bool) -> None:
        async with self._session.client(
            "s3", 
            **self._internal_kwargs
        ) as client:
            try:
                logger.info("Checking if the bucket is already created")
                await client.head_bucket(Bucket=bucket_name)
            except Exception:
                logger.info("Creating the bucket")
                await client.create_bucket(Bucket=bucket_name)

                if public:
                    public_policy = {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"AWS": ["*"]},
                                "Action": ["s3:GetObject"],
                                "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                            }
                        ]
                    }

                    await client.put_bucket_policy(
                        Bucket=bucket_name,
                        Policy=json.dumps(public_policy)
                    )

    async def generate_presigned_upload_url(
        self,
        bucket: str,
        key: str,
        content_type: str,
        expires_in: int = 300,
    ) -> str:
        async with self._session.client(
            "s3", **self._public_kwargs
        ) as client:
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
        async with self._session.client(
            "s3", **self._public_kwargs
        ) as client:
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

    async def delete_bucket(self, bucket_name: str) -> None:
        session = aioboto3.Session()
        async with session.client("s3", **self._internal_kwargs) as client:
            paginator = client.get_paginator("list_objects_v2")
            
            async for page in paginator.paginate(Bucket=bucket_name):
                for obj in page.get("Contents", []):
                    await client.delete_object(
                        Bucket=bucket_name, 
                        Key=obj["Key"]
                    )

            await client.delete_bucket(Bucket=bucket_name)

    async def delete_object(self, bucket: str, key: str) -> None:
        async with self._session.client(
            "s3", **self._internal_kwargs
        ) as client:
            await client.delete_object(Bucket=bucket, Key=key)
            logger.info(f"Deleted object with key: {key}")

    async def delete_image_variants(
        self, bucket: str, object_key: str
    ) -> None:
        """Deletes the original image and its generated variants"""
        await self.delete_object(
            bucket, object_key
        )
        for _, suffix in settings.IMAGE_SIZES:
            key = variant_key(object_key, suffix)
            await self.delete_object(
                bucket=bucket,
                key=key
            )
            logger.info(f"Deleted image file.\nBucket: {bucket}\n Key: {key}")
