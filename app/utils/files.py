from app.core.exceptions import InvalidFileTypeError


def to_megabytes(size_bytes: int) -> float:
    return size_bytes / (1024 * 1024)


def variant_key(
    object_key: str, suffix: str, extension: str = "webp"
) -> str:
    name = object_key.rsplit(".", 1)[0]
    return f"{name}_{suffix}.{extension}"


def validate_and_get_extension(
    allowed_content_types: dict[str, str],
    content_type: str
) -> str:
    """Retrieves and returns the extension based on the content type.
    
    *Raises*: InvalidFileTypeError if the content type isn't valid."""
    extension = allowed_content_types.get(content_type)

    if extension is None:
        raise InvalidFileTypeError
    
    return extension