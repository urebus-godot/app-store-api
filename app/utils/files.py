import shutil

from fastapi import UploadFile

from pathlib import Path
from app.core.logging import logger


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