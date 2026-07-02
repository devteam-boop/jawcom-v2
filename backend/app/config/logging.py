"""Logging configuration for the application."""

import logging
import sys
from typing import Any

from app.config.settings import get_settings

settings = get_settings()


def configure_logging() -> None:
    """Configure application logging."""
    # Remove default handlers
    logging.getLogger().handlers.clear()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    
    # Create formatter
    if settings.LOG_JSON:
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL)
    return logger
