import io

import boto3
from botocore.config import Config
from PIL import Image

from app.core.config import settings
from app.task_queue.celery_app import celery_app

THUMBNAIL_SIZE = (128, 128)
MEDIUM_SIZE = (640, 640)


def sync_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.MINIO_INTERNAL_ENDPOINT,
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def variant_key(object_key: str, suffix: str) -> str:
    # apps/xxx/icon/abc.jpg -> apps/xxx/icon/abc_thumb.webp
    # Ключ детерминированный — фронту не нужно ничего хранить в БД,
    # чтобы построить URL превью, достаточно знать соглашение об имени.
    stem = object_key.rsplit(".", 1)[0]
    return f"{stem}_{suffix}.webp"


@celery_app.task(
    name="tasks.generate_image_variants",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def generate_image_variants(self, bucket: str, object_key: str) -> None:
    client = sync_s3_client()

    try:
        response = client.get_object(Bucket=bucket, Key=object_key)
        original_bytes = response["Body"].read()
    except Exception as exc:
        # транзиентная сетевая ошибка/таймаут — ретраим, а не роняем таску
        raise self.retry(exc=exc)

    with Image.open(io.BytesIO(original_bytes)) as image:
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA")

        for size, suffix in ((THUMBNAIL_SIZE, "thumb"), (MEDIUM_SIZE, "medium")):
            variant = image.copy()
            variant.thumbnail(size)  # сохраняет пропорции, не растягивает

            buffer = io.BytesIO()
            variant.save(buffer, format="WEBP", quality=82)

            client.put_object(
                Bucket=bucket,
                Key=variant_key(object_key, suffix),
                Body=buffer.getvalue(),
                ContentType="image/webp",
            )
