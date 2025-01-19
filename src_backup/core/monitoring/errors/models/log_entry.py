"""Error logging models and data structures.

This module provides the core models for error logging and tracking, including
the LogEntry class for representing individual log entries with metadata.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any


class LogLevel(Enum):
    """Log levels for error and warning messages."""

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class LogEntry:
    """Represents a log entry in the error/warning log.

    This class provides a structured way to store and manage log entries,
    including metadata and serialization capabilities.

    Attributes:
        message: The log message
        log_level: Severity level of the log entry
        timestamp: When the log entry was created (UTC timezone)
        metadata: Additional contextual information

    Example:
        ```python
        from datetime import UTC, datetime

        entry = LogEntry(
            message="Database connection failed",
            log_level=LogLevel.ERROR,
            timestamp=datetime.now(UTC),  # Explicitly use UTC timezone
            metadata={"attempt": 3, "host": "db.example.com"}
        )
        ```
    """

    def __init__(
        self,
        message: str,
        log_level: LogLevel,
        timestamp: datetime,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a new log entry.

        Args:
            message: The log message
            log_level: Severity level of the log entry
            timestamp: When the log entry was created (UTC timezone)
            metadata: Additional contextual information
        """
        if timestamp.tzinfo != UTC:
            raise ValueError("Timestamp must be in UTC timezone")

        self.message = message
        self.log_level = log_level
        self.timestamp = timestamp
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert the log entry to a dictionary for storage.

        Returns:
            Dictionary representation of the log entry
        """
        return {
            "message": self.message,
            "level": self.log_level.value,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LogEntry":
        """Create a LogEntry instance from a dictionary.

        Args:
            data: Dictionary containing log entry data

        Returns:
            New LogEntry instance

        Example:
            ```python
            data = {
                "message": "Connection timeout",
                "level": "ERROR",
                "timestamp": datetime.now(UTC),
                "metadata": {"host": "api.example.com"}
            }
            entry = LogEntry.from_dict(data)
            ```
        """
        return cls(
            message=data["message"],
            log_level=LogLevel(data["level"]),
            timestamp=data["timestamp"],
            metadata=data.get("metadata", {}),
        )
