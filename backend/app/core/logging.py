"""Logging configuration for the GlasHaus backend."""

import logging

from app.core.config import LogLevel

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging(level: LogLevel) -> None:
    """Configure application logging without replacing existing handlers."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level))

    if not root_logger.handlers:
        logging.basicConfig(
            level=level,
            format=LOG_FORMAT,
        )
