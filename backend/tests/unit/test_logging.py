"""Unit tests for application logging."""

import logging

from app.core.logging import configure_logging


def test_configure_logging_sets_root_log_level() -> None:
    """Logging configuration must set the requested root log level."""
    root_logger = logging.getLogger()
    previous_level = root_logger.level

    try:
        configure_logging("DEBUG")
        assert root_logger.level == logging.DEBUG

        configure_logging("WARNING")
        assert root_logger.level == logging.WARNING
    finally:
        root_logger.setLevel(previous_level)
