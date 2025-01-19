"""Document lineage model.

This module provides the DocumentLineage model for tracking a document's complete history,
including transformations, processing steps, and relationships with other documents.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Transformation(Protocol):
    """Protocol for transformation operations."""

    def to_dict(self) -> dict[str, Any]:
        """Convert transformation to dictionary."""
        ...

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transformation":
        """Create from dictionary."""
        ...


@runtime_checkable
class ProcessingStep(Protocol):
    """Protocol for processing steps."""

    def to_dict(self) -> dict[str, Any]:
        """Convert step to dictionary."""
        ...

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProcessingStep":
        """Create from dictionary."""
        ...


@runtime_checkable
class LogEntry(Protocol):
    """Protocol for log entries."""

    def to_dict(self) -> dict[str, Any]:
        """Convert log entry to dictionary."""
        ...

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LogEntry":
        """Create from dictionary."""
        ...


@dataclass
class DocumentLineage:
    """Represents the complete lineage information for a document.

    This class serves as the main container for tracking a document's history,
    including its origin, transformations, processing steps, and relationships
    with other documents.

    Attributes:
        doc_id: Unique identifier for the document
        origin_id: ID of the original source document
        origin_source: Source system/location of the document
        origin_type: Type of the source document
        derived_from: ID of the parent document if derived
        derived_documents: IDs of documents derived from this one
        transformations: List of transformations applied
        processing_steps: List of processing operations performed
        error_logs: List of errors and warnings
        performance_metrics: Performance-related measurements
        metadata: Additional document metadata
        created_at: When the document was first tracked (UTC)
        last_modified: When the document was last changed (UTC)
        children: List of child document IDs
        parents: List of parent document IDs
    """

    doc_id: str
    origin_id: str | None = None
    origin_source: str | None = None
    origin_type: str | None = None
    derived_from: str | None = None
    derived_documents: list[str] = field(default_factory=list)
    transformations: list[Transformation] = field(default_factory=list)
    processing_steps: list[ProcessingStep] = field(default_factory=list)
    error_logs: list[LogEntry] = field(default_factory=list)
    performance_metrics: dict[str, Any] = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_modified: datetime = field(default_factory=lambda: datetime.now(UTC))
    children: list[str] = field(default_factory=list)
    parents: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert the document lineage to a dictionary."""
        return {
            "doc_id": self.doc_id,
            "origin_id": self.origin_id,
            "origin_source": self.origin_source,
            "origin_type": self.origin_type,
            "derived_from": self.derived_from,
            "derived_documents": self.derived_documents,
            "transformations": [t.to_dict() for t in self.transformations],
            "processing_steps": [p.to_dict() for p in self.processing_steps],
            "error_logs": [e.to_dict() for e in self.error_logs],
            "performance_metrics": self.performance_metrics,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "children": self.children,
            "parents": self.parents,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocumentLineage":
        """Create a DocumentLineage instance from a dictionary."""
        # Convert datetime strings to datetime objects
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("last_modified"), str):
            data["last_modified"] = datetime.fromisoformat(data["last_modified"])

        # Convert error logs from dict to LogEntry objects
        error_logs = [
            LogEntry.from_dict(log) if isinstance(log, dict) else log
            for log in data.get("error_logs", [])
        ]
        data["error_logs"] = error_logs

        # Convert transformations from dict to Transformation objects
        transformations = [
            Transformation.from_dict(t) if isinstance(t, dict) else t
            for t in data.get("transformations", [])
        ]
        data["transformations"] = transformations

        # Convert processing steps from dict to ProcessingStep objects
        processing_steps = [
            ProcessingStep.from_dict(p) if isinstance(p, dict) else p
            for p in data.get("processing_steps", [])
        ]
        data["processing_steps"] = processing_steps

        return cls(**data)
