import os

from fastapi import UploadFile

from pathlib import Path
from app.core.logging import logger


def write_file(
    file: UploadFile,
    filename: str,
    path: Path,
    chunk_size_kb: int = 1024
) -> Path:
    path.mkdir(exist_ok=True)
    file_path = path / filename
    file_path.touch()

    logger.info(f"Created File! Path for file: {file_path}")

    with open(file_path, "wb") as buffer:
        logger.info("Start writing to disk")
        while chunk := file.file.read(1024 * chunk_size_kb):
            buffer.write(chunk)
            logger.info(
                f"Wrote chunk to buffer: {chunk[:30]}..."
                f"Length: {len(chunk)}"
                )

    return file_path


def to_megabytes(size_bytes: int) -> float:
    return size_bytes / 1048576