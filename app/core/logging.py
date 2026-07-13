import logging
from logging import Logger

from app.core.config import settings


def setup_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s | %(name)s %(levelname)s : %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=settings.LOGGING_LEVEL,
        filename=settings.LOG_FILE_PATH,
    )

def get_logger() -> Logger:
    logger = logging.getLogger("app_logger")
    logger.setLevel(settings.LOGGING_LEVEL)
    return logger


logger = get_logger()
