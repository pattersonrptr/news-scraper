import logging
import sys
from typing import Any

import structlog

from .config import get_settings


def setup_logging() -> None:
    """Initialize and configure structured logging for the application.

    This function configures structlog and the stdlib logging handlers based on
    values from the application settings. Call this once during application
    startup (before creating loggers).
    """
    settings = get_settings()

    timestamper = structlog.processors.TimeStamper(fmt="iso")

    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        timestamper,
        structlog.processors.add_log_level,
    ]

    if settings.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, settings.log_level)),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to forward to structlog
    log_level = getattr(logging, settings.log_level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    logging.basicConfig(level=log_level, handlers=[handler])


def get_logger(name: str | None = None):
    """Return a structlog logger bound to the given name."""
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()
