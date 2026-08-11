from fastapi import UploadFile

from app.core.exceptions import invalid_file_exception




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