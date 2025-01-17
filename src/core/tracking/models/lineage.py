"""
Document lineage tracking.

This module provides the DocumentLineage model for tracking a document's complete history,
including transformations, processing steps, and relationships with other documents.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from src.core.tracking.enums import ProcessingStatus, TransformationType
from src.core.tracking.models.logging import LogEntry
from src.core.tracking.models.processing import ProcessingStep
from src.core.tracking.models.transformation import Transformation


@dataclass
class DocumentLineage:
    """
    Represents the complete lineage information for a document.

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

    Example:
        ```python
        lineage = DocumentLineage(
            doc_id="doc123",
            origin_source="file_system",
            origin_type="pdf",
            metadata={
                "title": "Annual Report",
                "pages": 10,
                "author": "John Doe"
            }
        )

        # Add processing history
        lineage.processing_steps.append(
            ProcessingStep(
                step_name="text_extraction",
                status=ProcessingStatus.SUCCESS
            )
        )

        # Record transformations
        lineage.transformations.append(
            Transformation(
                transform_type=TransformationType.CONTENT,
                description="Converted to plain text"
            )
        )
        ```
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

    def __init__(
        self,
        doc_id: str,
        origin_id: str | None = None,
        origin_source: str | None = None,
        origin_type: str | None = None,
        derived_from: str | None = None,
        derived_documents: list[str] | None = None,
        transformations: list[Transformation] | None = None,
        processing_steps: list[ProcessingStep] | None = None,
        error_logs: list[LogEntry] | None = None,
        performance_metrics: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        last_modified: datetime | None = None,
        children: list[str] | None = None,
        parents: list[str] | None = None,
    ):
        self.doc_id = doc_id
        self.origin_id = origin_id
        self.origin_source = origin_source
        self.origin_type = origin_type
        self.derived_from = derived_from
        self.derived_documents = derived_documents or []
        self.transformations = transformations or []
        self.processing_steps = processing_steps or []
        self.error_logs = error_logs or []
        self.performance_metrics = performance_metrics or {}
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(UTC)
        self.last_modified = last_modified or datetime.now(UTC)
        self.children = children or []
        self.parents = parents or []

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
