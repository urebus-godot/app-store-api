from pathlib import Path
from typing import Optional

from PIL import Image

from app.core.logging import logger

from app.task_queue.celery_app import celery_app


@celery_app.task(name="tasks.process_image")
def process_image(
    path: str, 
    size: Optional[tuple[int, int]] = None,
    quality: int = 75
    ):
    path = Path(path)
    with Image.open(path) as img:
        logger.info(f"\n\n{path}\n\n")
        img = img.convert("RGB")
        if size is not None:
            img.thumbnail(size)
        img.save(path, quality=quality)
        logger.info(f"Saved image.\nSize: {img.size}\nMode: {img.mode}")
