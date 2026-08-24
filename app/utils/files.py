
from app.core.exceptions import invalid_file_exception


def to_megabytes(size_bytes: int) -> float:
    return size_bytes / 1048576


def to_bytes(size_megabytes: int) -> float:
    return size_megabytes * 1048576


def variant_key(object_key: str, suffix: str) -> str:
    stem = object_key.rsplit(".", 1)[0]
    return f"{stem}_{suffix}.webp"


def validate_and_get_extension(
    allowed_content_types: dict[str, str],
    content_type: str
) -> str:
    extension = allowed_content_types.get(content_type)
    if extension is None:
        raise invalid_file_exception
    return extension