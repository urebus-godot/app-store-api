import logging
from contextvars import ContextVar

from typing import Any, Literal
import sys


request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
user_id_var: ContextVar[str] = ContextVar("user_id", default="-")
 

class RequestContextFilter(logging.Filter):
    """Прокидывает request_id/user_id из contextvars в каждый LogRecord."""
 
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        record.user_id = user_id_var.get()
        return True


def build_logging_config(
    env: Literal["local", "production"] = "local",
    level: str = "INFO",
) -> dict[str, Any]:
    json_logs = env == "production"
    formatter = "json" if json_logs else "console"
 
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_context": {"()": RequestContextFilter},
        },
        "formatters": {
            "console": {
                "format": (
                    "%(asctime)s | %(levelname)-8s | %(name)s | "
                    "rid=%(request_id)s uid=%(user_id)s | %(message)s"
                ),
                "datefmt": "%H:%M:%S",
            },
            "json": {
                # pip/uv install python-json-logger
                "()": "pythonjsonlogger.json.JsonFormatter",
                "format": (
                    "%(asctime)s %(levelname)s %(name)s "
                    "%(request_id)s %(user_id)s %(message)s"
                ),
            },
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": formatter,
                "filters": ["request_context"],
                "stream": sys.stdout,
            },
        },
        "root": {
            "handlers": ["default"],
            "level": level,
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["default"], "level": level, "propagate": False
                },
            "uvicorn.access": {
                "handlers": ["default"], "level": "WARNING", 
                "propagate": False
                },
            "sqlalchemy.engine": {
                "handlers": ["default"], "level": "WARNING", 
                "propagate": False
                },
            "app": {
                "handlers": ["default"], "level": level, "propagate": False
                },
            "celery": {
                "handlers": ["default"], "level": level, "propagate": False
                },
        },
    }


def setup_logging(
    env: Literal["local", "production"] = "local", 
    level: str = "INFO"
) -> None:
    logging.config.dictConfig(build_logging_config(env=env, level=level))