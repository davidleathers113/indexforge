"""
Enumerations used in the document lineage tracking system.

This module defines reusable enumeration classes for:
- Document transformation types
- Processing statuses
- Logging levels
- Health statuses
- Reference types
"""

from enum import Enum


class TransformationType(str, Enum):
    """Type of transformation applied to a document."""

    CHUNKING = "chunking"
    METADATA_UPDATE = "metadata_update"
    CONTENT_ENRICHMENT = "content_enrichment"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    EXTRACTION = "extraction"
    MERGE = "merge"
    SPLIT = "split"
    CUSTOM = "custom"
    TEXT_EXTRACTION = "text_extraction"
    FORMAT_CONVERSION = "format_conversion"
    CONTENT = "content"
    METADATA = "metadata"
    STRUCTURE = "structure"


class ProcessingStatus(str, Enum):
    """Status of a processing step."""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    RUNNING = "running"
    FAILED = "failed"
    QUEUED = "queued"


class LogLevel(Enum):
    """Log levels for error and warning logs."""

    ERROR = "error"
    WARNING = "warning"


class HealthStatus(Enum):
    """Health status values for system health checks."""

    HEALTHY = ("healthy", 0)
    WARNING = ("warning", 1)
    CRITICAL = ("critical", 2)

    def __init__(self, status: str, value: int):
        self._status = status
        self._value = value

    @property
    def status(self) -> str:
        return self._status

    def __lt__(self, other):
        if not isinstance(other, HealthStatus):
            return NotImplemented
        return self._value < other._value

    def __gt__(self, other):
        if not isinstance(other, HealthStatus):
            return NotImplemented
        return self._value > other._value

    def __le__(self, other):
        if not isinstance(other, HealthStatus):
            return NotImplemented
        return self._value <= other._value

    def __ge__(self, other):
        if not isinstance(other, HealthStatus):
            return NotImplemented
        return self._value >= other._value

    def __str__(self):
        return self._status


class ReferenceType(Enum):
    """Types of references between chunks."""

    SEQUENTIAL = "sequential"  # Next/previous in sequence
    SEMANTIC = "semantic"  # Content similarity
    TOPIC = "topic"  # Same topic cluster
    CITATION = "citation"  # Direct citation/quote
