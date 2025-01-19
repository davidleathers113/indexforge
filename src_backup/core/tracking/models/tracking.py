"""Tracking model implementations.

This module provides concrete implementations of tracking-related models
that satisfy the protocols defined in core models.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class TransformationType(Enum):
    """Types of document transformations."""

    CONTENT = "content"
    STRUCTURE = "structure"
    FORMAT = "format"
    METADATA = "metadata"


@dataclass
class Transformation:
    """Represents a transformation applied to a document."""

    transform_type: TransformationType
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert transformation to dictionary."""
        return {
            "transform_type": self.transform_type.value,
            "description": self.description,
            "parameters": self.parameters,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transformation":
        """Create from dictionary."""
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        data["transform_type"] = TransformationType(data["transform_type"])
        return cls(**data)


class ProcessingStatus(Enum):
    """Status of processing operations."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ProcessingStep:
    """Represents a processing step applied to a document."""

    step_name: str
    status: ProcessingStatus
    details: dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: datetime | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert processing step to dictionary."""
        return {
            "step_name": self.step_name,
            "status": self.status.value,
            "details": self.details,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProcessingStep":
        """Create from dictionary."""
        if isinstance(data.get("start_time"), str):
            data["start_time"] = datetime.fromisoformat(data["start_time"])
        if isinstance(data.get("end_time"), str):
            data["end_time"] = datetime.fromisoformat(data["end_time"])
        data["status"] = ProcessingStatus(data["status"])
        return cls(**data)


class LogLevel(Enum):
    """Log entry severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    """Represents a log entry in the document's history."""

    level: LogLevel
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert log entry to dictionary."""
        return {
            "level": self.level.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LogEntry":
        """Create from dictionary."""
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        data["level"] = LogLevel(data["level"])
        return cls(**data)
