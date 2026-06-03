"""Logging configuration for the inference service."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import structlog
from structlog.dev import ConsoleRenderer
from structlog.processors import JSONRenderer
from structlog.types import EventDict, Processor

from .config import settings


def drop_color_message_key(_, __, event_dict: EventDict) -> EventDict:
    event_dict.pop("color_message", None)
    return event_dict


def file_log_filter_processors(_, __, event_dict: EventDict) -> EventDict:
    if not settings.FILE_LOG_INCLUDE_REQUEST_ID:
        event_dict.pop("request_id", None)
    if not settings.FILE_LOG_INCLUDE_PATH:
        event_dict.pop("path", None)
    if not settings.FILE_LOG_INCLUDE_METHOD:
        event_dict.pop("method", None)
    if not settings.FILE_LOG_INCLUDE_CLIENT_HOST:
        event_dict.pop("client_host", None)
    if not settings.FILE_LOG_INCLUDE_STATUS_CODE:
        event_dict.pop("status_code", None)
    return event_dict


def console_log_filter_processors(_, __, event_dict: EventDict) -> EventDict:
    if not settings.CONSOLE_LOG_INCLUDE_REQUEST_ID:
        event_dict.pop("request_id", None)
    if not settings.CONSOLE_LOG_INCLUDE_PATH:
        event_dict.pop("path", None)
    if not settings.CONSOLE_LOG_INCLUDE_METHOD:
        event_dict.pop("method", None)
    if not settings.CONSOLE_LOG_INCLUDE_CLIENT_HOST:
        event_dict.pop("client_host", None)
    if not settings.CONSOLE_LOG_INCLUDE_STATUS_CODE:
        event_dict.pop("status_code", None)
    return event_dict


timestamper = structlog.processors.TimeStamper(fmt="iso")
SHARED_PROCESSORS: list[Processor] = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.stdlib.ExtraAdder(),
    drop_color_message_key,
    timestamper,
    structlog.processors.StackInfoRenderer(),
]

structlog.configure(
    processors=SHARED_PROCESSORS + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


def build_formatter(*, json_output: bool, pre_chain: list[Processor]) -> structlog.stdlib.ProcessorFormatter:
    renderer = JSONRenderer() if json_output else ConsoleRenderer()
    processors = [structlog.stdlib.ProcessorFormatter.remove_processors_meta, renderer]

    if json_output:
        pre_chain = pre_chain + [structlog.processors.format_exc_info]

    return structlog.stdlib.ProcessorFormatter(foreign_pre_chain=pre_chain, processors=processors)


LOG_DIR = Path(settings.FILE_LOG_DIR or Path.cwd() / "logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

file_handler = RotatingFileHandler(
    filename=LOG_DIR / "app.log",
    maxBytes=settings.FILE_LOG_MAX_BYTES,
    backupCount=settings.FILE_LOG_BACKUP_COUNT,
)
file_handler.setLevel(settings.FILE_LOG_LEVEL)
file_handler.setFormatter(
    build_formatter(
        json_output=settings.FILE_LOG_FORMAT_JSON, pre_chain=SHARED_PROCESSORS + [file_log_filter_processors]
    )
)

console_handler = logging.StreamHandler()
console_handler.setLevel(settings.CONSOLE_LOG_LEVEL)
console_handler.setFormatter(
    build_formatter(
        json_output=settings.CONSOLE_LOG_FORMAT_JSON, pre_chain=SHARED_PROCESSORS + [console_log_filter_processors]
    )
)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers.clear()
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

for logger_name in ("celery", "celery.app.trace"):
    logger = logging.getLogger(logger_name)
    logger.handlers.clear()
    logger.propagate = True
    logger.setLevel(logging.INFO)
