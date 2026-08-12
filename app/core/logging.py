import logging

from app.core.config import settings


def setup_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s | %(name)s %(levelname)s : %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=settings.LOGGING_LEVEL,
        filename=settings.LOG_FILE_PATH,
    )
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s %(levelname)s : %(message)s"
    )
