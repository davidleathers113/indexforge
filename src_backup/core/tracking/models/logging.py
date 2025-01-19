"""
Document processing log entries.

This module provides the LogEntry model for tracking errors, warnings, and other
notable events that occur during document processing.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from src.core.tracking.enums import LogLevel


@dataclass
class LogEntry:
    """
    Represents an error or warning log entry.

    This class stores information about errors, warnings, and other notable events
    that occur during document processing.

    Attributes:
        log_level: Severity of the log entry (error/warning)
        message: Description of what occurred
        timestamp: When the event occurred (UTC)
        metadata: Additional context about the event

    Example:
        ```python
        log = LogEntry(
            log_level=LogLevel.WARNING,
            message="Low image quality detected",
            metadata={"quality_score": 0.4}
        )
        ```
    """

    log_level: LogLevel
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict = field(default_factory=dict)

    def __init__(
        self,
        log_level: LogLevel,
        message: str,
        timestamp: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.log_level = log_level
        self.message = message
        self.timestamp = timestamp or datetime.now(UTC)
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert the log entry to a dictionary for serialization."""
        return {
            "level": self.log_level.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LogEntry":
        """Create a log entry from a dictionary."""
        return cls(
            log_level=LogLevel(data["level"]),
            message=data["message"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )
