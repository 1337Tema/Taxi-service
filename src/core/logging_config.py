"""Конфигурация структурированного логирования для приложения."""

import logging
from logging.config import dictConfig
import sys

# Формат лога в виде словаря (удобно для парсинга)
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(module)s %(funcName)s %(lineno)d %(message)s %(request_id)s"
        },
        "default": {
            "format": "[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s"
        }
    },
    "handlers": {
        "console_json": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "json",
        },
        "console_default": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "default",
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console_default"],
    },
    "loggers": {
        "uvicorn": {"handlers": ["console_default"], "level": "INFO", "propagate": False},
        "fastapi": {"handlers": ["console_json"], "level": "INFO", "propagate": False},
        "src": {"handlers": ["console_json"], "level": "INFO", "propagate": False},
    },
}


def setup_logging():
    dictConfig(LOG_CONFIG)


# Фильтр для добавления request_id в логи
class RequestIdFilter(logging.Filter):
    def __init__(self, name: str = "", request_id_storage=None):
        super().__init__(name)
        self.request_id_storage = request_id_storage

    def filter(self, record):
        try:
            record.request_id = self.request_id_storage.get()
        except Exception:
            record.request_id = "N/A"
        return True