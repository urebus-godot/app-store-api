import logging

from app.core.config import settings


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("app logger")
    logger.setLevel(settings.LOGGING_LEVEL)

    logging.basicConfig(
        format="%(asctime)s | %(name)s %(levelname)s : %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=settings.LOGGING_LEVEL,
        filename=settings.LOG_FILE_PATH,
    )

    return logger


logger = setup_logging()
