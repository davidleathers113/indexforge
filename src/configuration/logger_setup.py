"""Logging configuration and setup module.

This module provides functionality for setting up and configuring logging in the
application, including standard logging and JSON-formatted logging with rotation
and context support. It includes utilities for both file and console logging.
"""

from datetime import datetime
import json
import logging
import logging.handlers
import os
import threading


def setup_logger(
    name: str,
    log_path: str | None = None,
    level: int = logging.INFO,
    format_string: str | None = None,
    rotate: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """Set up a logger with console and optional file output.

    Configures a logger with the specified name and handlers. Can output to
    both console and file, with optional log rotation and custom formatting.

    Args:
        name: Name of the logger to create.
        log_path: Optional path to log file. If None, only console logging is used.
        level: Logging level (default: logging.INFO).
        format_string: Optional custom format string for log messages.
        rotate: Whether to use rotating file handler (default: True).
        max_bytes: Maximum size in bytes before rotating (default: 10MB).
        backup_count: Number of backup files to keep (default: 5).

    Returns:
        logging.Logger: Configured logger instance.

    Example:
        ```python
        logger = setup_logger(
            name="app_logger",
            log_path="/var/log/app.log",
            level=logging.DEBUG,
            rotate=True
        )
        logger.info("Application started")
        ```
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear any existing handlers
    logger.handlers = []

    # Default format
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(format_string)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if path provided)
    if log_path:
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(log_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        if rotate:
            file_handler = logging.handlers.RotatingFileHandler(
                log_path, maxBytes=max_bytes, backupCount=backup_count
            )
        else:
            file_handler = logging.FileHandler(log_path)

        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


class JsonFormatter(logging.Formatter):
    """Format log records as JSON objects.

    Custom formatter that converts log records into JSON format, including
    timestamp, log level, logger name, message, and any additional context
    fields or exception information.

    Attributes:
        _lock (threading.Lock): Lock for thread-safe formatting
    """

    def __init__(self):
        """Initialize the formatter with a thread lock."""
        super().__init__()
        self._lock = threading.Lock()

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string.

        Thread-safe implementation that converts a logging.LogRecord object into
        a JSON string containing all relevant logging information and any
        additional context.

        Args:
            record: The log record to format.

        Returns:
            str: JSON-formatted string containing the log data.
        """
        with self._lock:
            # Basic log data
            log_data = {
                "timestamp": datetime.utcnow().timestamp(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }

            # Add exception info if present
            if record.exc_info and isinstance(record.exc_info, tuple):
                exc_type, exc_value, exc_traceback = record.exc_info
                log_data["exception"] = {
                    "type": exc_type.__name__,
                    "message": str(exc_value),
                    "traceback": self.formatException(record.exc_info),
                }

            # Add extra fields from both record attributes and extra_fields
            if hasattr(record, "extra_fields"):
                log_data.update(record.extra_fields)

            # Add any other attributes that were set directly on the record
            for key, value in record.__dict__.items():
                if (
                    key not in log_data
                    and not key.startswith("_")
                    and key not in {"msg", "args", "exc_info", "exc_text", "extra_fields"}
                ):
                    log_data[key] = value

            return json.dumps(log_data)


def setup_json_logger(
    name: str,
    log_path: str,
    level: int = logging.INFO,
    rotate: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """Set up a logger with JSON formatting and file output.

    Creates a logger that outputs JSON-formatted log records to a file,
    with optional log rotation support.

    Args:
        name: Name of the logger to create.
        log_path: Path to the JSON log file.
        level: Logging level (default: logging.INFO).
        rotate: Whether to use rotating file handler (default: True).
        max_bytes: Maximum size in bytes before rotating (default: 10MB).
        backup_count: Number of backup files to keep (default: 5).

    Returns:
        logging.Logger: Configured logger instance with JSON formatting.

    Example:
        ```python
        logger = setup_json_logger(
            name="json_logger",
            log_path="/var/log/app.json",
            level=logging.INFO
        )
        logger.info("Application started")
        ```
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear any existing handlers
    logger.handlers = []

    # Create formatter
    formatter = JsonFormatter()

    # File handler
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    if rotate:
        file_handler = logging.handlers.RotatingFileHandler(
            log_path, maxBytes=max_bytes, backupCount=backup_count
        )
    else:
        file_handler = logging.FileHandler(log_path)

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def log_with_context(
    logger: logging.Logger, level: int, message: str, extra_fields: dict | None = None
):
    """Log a message with additional context fields in JSON format.

    Creates a log record with additional context fields and formats it as JSON
    if a JSON formatter is available, otherwise falls back to standard logging.
    Thread-safe implementation that ensures consistent timestamp ordering.

    Args:
        logger: Logger instance to use for logging.
        level: Logging level for the message.
        message: The log message.
        extra_fields: Optional dictionary of additional fields to include.
    """
    if extra_fields is None:
        extra_fields = {}

    # Add timestamp as float for ordering
    current_time = datetime.utcnow().timestamp()
    extra_fields["timestamp"] = current_time

    # Create a LogRecord with extra fields
    record = logging.LogRecord(
        name=logger.name,
        level=level,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None,
    )

    # Add extra fields to the record
    for key, value in extra_fields.items():
        setattr(record, key, value)
    record.extra_fields = extra_fields

    # Find the appropriate handler and format
    for handler in logger.handlers:
        if isinstance(handler.formatter, JsonFormatter):
            handler.handle(record)
            return

    # If no JSON formatter found, log normally with repr of extra fields
    if extra_fields:
        message = "%s %s" % (message, repr(extra_fields))
    logger.log(level, message)
