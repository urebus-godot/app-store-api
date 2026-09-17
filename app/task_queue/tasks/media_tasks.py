import io

import boto3
from botocore.config import Config
from PIL import Image, UnidentifiedImageError

from app.core.config import settings
from app.task_queue.celery_app import celery_app

from app.utils.files import variant_key


def get_boto3_client(
    endpoint_url: str = settings.MINIO_INTERNAL_ENDPOINT, 
    access_key: str = settings.MINIO_ACCESS_KEY, 
    secret_key: str = settings.MINIO_SECRET_KEY
):
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


@celery_app.task(
    name="media_tasks.generate_image_variants",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def generate_image_variants(
    self, bucket: str, object_key: str,
    endpoint_url: str = settings.MINIO_INTERNAL_ENDPOINT, 
    access_key: str = settings.MINIO_ACCESS_KEY, 
    secret_key: str = settings.MINIO_SECRET_KEY
) -> None:
    client = get_boto3_client(
        endpoint_url, access_key, secret_key
    )
    try:
        response = client.get_object(Bucket=bucket, Key=object_key)
        original_bytes = response["Body"].read()
    except Exception as exc:
        raise self.retry(exc=exc)

    try:
        with Image.open(io.BytesIO(original_bytes)) as image:
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGBA")

            for size, suffix in settings.IMAGE_SIZES:
                variant = image.copy()
                variant.thumbnail(size)

                buffer = io.BytesIO()
                variant.save(buffer, format="WEBP", quality=82)

                client.put_object(
                    Bucket=bucket,
                    Key=variant_key(object_key, suffix),
                    Body=buffer.getvalue(),
                    ContentType="image/webp",
                )
    except UnidentifiedImageError:
        pass
