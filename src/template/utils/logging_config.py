"""Logging configuration for code cleanup utility."""

from dataclasses import dataclass, field
from enum import Enum
import logging
import logging.handlers
import os
from pathlib import Path
import sys
from typing import Dict, Optional, Union


class LogLevel(Enum):
    """Log level options."""

    QUIET = logging.WARNING
    NORMAL = logging.INFO
    VERBOSE = logging.DEBUG


@dataclass
class LogRotationConfig:
    """Configuration for log file rotation."""

    max_bytes: int = 1024 * 1024  # 1MB
    backup_count: int = 5
    compress: bool = True
    encoding: str = "utf-8"

    def validate(self) -> None:
        """Validate log rotation configuration."""
        if not isinstance(self.max_bytes, int) or self.max_bytes < 0:
            raise ValueError("max_bytes must be a non-negative integer")
        if not isinstance(self.backup_count, int) or self.backup_count < 0:
            raise ValueError("backup_count must be a non-negative integer")
        if not isinstance(self.compress, bool):
            raise ValueError("compress must be a boolean")
        if not isinstance(self.encoding, str):
            raise ValueError("encoding must be a string")


@dataclass
class LogConfig:
    """Logging configuration."""

    level: LogLevel = LogLevel.NORMAL
    format: str = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    file_path: Optional[Union[str, Path]] = None
    rotation_config: Optional[LogRotationConfig] = None
    extra_fields: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize configuration with defaults."""
        if self.rotation_config is None and self.file_path:
            self.rotation_config = LogRotationConfig()

    def validate(self) -> None:
        """Validate logging configuration."""
        if not isinstance(self.level, LogLevel):
            raise ValueError("level must be a LogLevel enum value")
        if not isinstance(self.format, str):
            raise ValueError("format must be a string")
        if not isinstance(self.date_format, str):
            raise ValueError("date_format must be a string")
        if self.file_path and not isinstance(self.file_path, (str, Path)):
            raise ValueError("file_path must be a string or Path")
        if self.rotation_config:
            self.rotation_config.validate()
        if not isinstance(self.extra_fields, dict):
            raise ValueError("extra_fields must be a dictionary")


def setup_logging(config: Optional[LogConfig] = None) -> logging.Logger:
    """Configure and return the logger.

    Args:
        config: Optional logging configuration

    Returns:
        logging.Logger: Configured logger instance
    """
    if config is None:
        config = LogConfig()

    config.validate()

    # Configure logging
    handlers = []

    # Console handler with color support
    console_handler = _create_console_handler(config)
    handlers.append(console_handler)

    # File handler if specified
    if config.file_path:
        file_handler = _create_file_handler(config)
        handlers.append(file_handler)

    # Get logger for this module
    logger = logging.getLogger(__name__)
    logger.setLevel(config.level.value)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Add configured handlers
    for handler in handlers:
        logger.addHandler(handler)

    if config.level == LogLevel.QUIET:
        logger.debug = lambda *args, **kwargs: None
        logger.info = lambda *args, **kwargs: None

    # Add extra context
    logger = _add_extra_context(logger, config)

    return logger


def _create_console_handler(config: LogConfig) -> logging.Handler:
    """Create a console handler with optional color support.

    Args:
        config: Logging configuration

    Returns:
        logging.Handler: Configured console handler
    """
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(config.level.value)

    # Use colored formatter if available
    try:
        import colorlog

        formatter = colorlog.ColoredFormatter(
            f"%(log_color)s{config.format}%(reset)s",
            datefmt=config.date_format,
            reset=True,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    except ImportError:
        formatter = logging.Formatter(config.format, datefmt=config.date_format)

    console_handler.setFormatter(formatter)
    return console_handler


def _create_file_handler(config: LogConfig) -> logging.Handler:
    """Create a file handler with rotation support.

    Args:
        config: Logging configuration

    Returns:
        logging.Handler: Configured file handler
    """
    if config.rotation_config:
        handler = logging.handlers.RotatingFileHandler(
            config.file_path,
            maxBytes=config.rotation_config.max_bytes,
            backupCount=config.rotation_config.backup_count,
            encoding=config.rotation_config.encoding,
        )
    else:
        handler = logging.FileHandler(config.file_path)

    handler.setLevel(config.level.value)
    handler.setFormatter(logging.Formatter(config.format, datefmt=config.date_format))
    return handler


def _add_extra_context(logger: logging.Logger, config: LogConfig) -> logging.Logger:
    """Add extra context to logger.

    Args:
        logger: Logger instance
        config: Logging configuration

    Returns:
        logging.Logger: Logger with extra context
    """
    # Add process and environment information
    extra = {
        "pid": os.getpid(),
        "hostname": os.uname().nodename,
        "python_version": sys.version.split()[0],
        **config.extra_fields,
    }

    # Create adapter with extra fields
    logger = logging.LoggerAdapter(logger, extra)

    return logger
