import shutil
from pathlib import Path

from fastapi import UploadFile

from app.core.logging import logger
from app.core.exceptions import invalid_file_exception


def write_file(
    file: UploadFile,
    filename: str,
    path: Path,
    chunk_size_kb: int = 1024
) -> None:
    path.mkdir(exist_ok=True)
    file_path = path / filename
    file_path.touch()

    logger.info(f"Created File! Path for file: {file_path}")

    with open(file_path, "wb") as buffer:
        logger.info("Start writing to disk")
        shutil.copyfileobj(file.file, buffer, chunk_size_kb * 1024)


def to_megabytes(size_bytes: int) -> float:
    return size_bytes / 1048576


def validate_and_get_extension(
    allowed_content_types: dict[str, str],
    content_type: str
) -> str:
    extension = allowed_content_types.get(content_type)
    if extension is None:
        raise invalid_file_exception
    return extension