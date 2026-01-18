"""
Logging configuration for Aura backend
"""

import logging
import sys
from typing import Any
from app.config import settings


def setup_logging() -> None:
    """Configure application logging"""

    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Create formatter
    if settings.ENVIRONMENT == "production":
        # JSON format for production (easier to parse)
        formatter = logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", '
            '"function": "%(funcName)s", "line": %(lineno)d, "message": "%(message)s"}',
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        # Human-readable format for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set levels for third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    # Set app loggers
    logging.getLogger("app").setLevel(log_level)

    logging.info(f"Logging configured: level={settings.LOG_LEVEL}, environment={settings.ENVIRONMENT}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(f"app.{name}")
