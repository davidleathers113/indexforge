"""
Data models for document lineage tracking.

This module defines the core data structures used throughout the document lineage system.
It provides dataclasses for representing document transformations, processing steps,
error logs, and relationships between documents and chunks.

Key Models:
    - ProcessingStep: Track individual processing operations
    - Transformation: Record document transformations
    - LogEntry: Store error and warning logs
    - DocumentLineage: Main container for document history
    - ChunkReference: Track relationships between document chunks
    - HealthCheckResult: System health check results

Example:
    ```python
    # Create a document lineage record
    lineage = DocumentLineage(
        doc_id="doc123",
        origin_source="file_system",
        origin_type="pdf",
        metadata={"pages": 10}
    )

    # Add a processing step
    step = ProcessingStep(
        step_name="text_extraction",
        status=ProcessingStatus.SUCCESS,
        details={"chars": 5000}
    )
    lineage.processing_steps.append(step)

    # Record a transformation
    transform = Transformation(
        transform_type=TransformationType.CONTENT,
        description="Converted to plain text",
        parameters={"format": "txt"}
    )
    lineage.transformations.append(transform)
    ```
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .enums import LogLevel, ProcessingStatus, ReferenceType, TransformationType


@dataclass
class ProcessingStep:
    """
    Represents a processing step applied to a document.

    This class tracks individual processing operations performed on a document,
    including their status, timing, and any associated metadata.

    Attributes:
        step_name: Name of the processing step (e.g., "text_extraction")
        status: Current status of the step (success, error, etc.)
        timestamp: When the step was executed (UTC)
        details: Step-specific details like metrics or results
        metadata: Additional metadata about the step

    Example:
        ```python
        step = ProcessingStep(
            step_name="text_extraction",
            status=ProcessingStatus.SUCCESS,
            details={"chars": 5000, "pages": 10},
            metadata={"processor_version": "1.2.3"}
        )
        ```
    """

    step_name: str
    status: ProcessingStatus
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    details: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the processing step to a dictionary."""
        return {
            "step_name": self.step_name,
            "status": self.status.value,  # Convert enum to string
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "metadata": self.metadata,
        }


@dataclass
class Transformation:
    """
    Represents a transformation applied to a document.

    This class records changes made to a document's content or structure,
    tracking the type of transformation, when it occurred, and relevant parameters.

    Attributes:
        transform_type: Type of transformation applied
        timestamp: When the transformation occurred (UTC)
        description: Human-readable description of the change
        parameters: Parameters used in the transformation
        metadata: Additional metadata about the transformation

    Example:
        ```python
        transform = Transformation(
            transform_type=TransformationType.CONTENT,
            description="Converted to plain text",
            parameters={"format": "txt", "encoding": "utf-8"},
            metadata={"transformer_version": "2.0.0"}
        )
        ```
    """

    transform_type: TransformationType
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    description: str = ""
    parameters: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the transformation to a dictionary."""
        return {
            "transform_type": self.transform_type.value,  # Convert enum to string
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "parameters": self.parameters,
            "metadata": self.metadata,
        }


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
        self.children = children or []  # Initialize children from parameter
        self.parents = parents or []  # Initialize parents from parameter

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


@dataclass
class ChunkReference:
    """
    Represents a reference between two document chunks.

    This class tracks relationships between different chunks of content,
    including similarity scores and topic associations.

    Attributes:
        source_id: ID of the source chunk
        target_id: ID of the target chunk
        ref_type: Type of reference relationship
        similarity_score: Optional similarity measure (0-1)
        topic_id: Optional ID of shared topic
        created_at: When the reference was created (UTC)
        metadata: Additional reference metadata

    Example:
        ```python
        ref = ChunkReference(
            source_id="chunk123",
            target_id="chunk456",
            ref_type=ReferenceType.SIMILAR,
            similarity_score=0.85,
            topic_id=42,
            metadata={"method": "cosine_similarity"}
        )
        ```
    """

    source_id: str
    target_id: str
    ref_type: ReferenceType
    similarity_score: float | None = None
    topic_id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the chunk reference to a dictionary."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "ref_type": self.ref_type.value,  # Convert enum to string
            "similarity_score": self.similarity_score,
            "topic_id": self.topic_id,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class HealthCheckResult:
    """
    Result of a system health check.

    This class contains the results of a system health check, including overall
    status, any issues found, and various metrics about system performance.

    Attributes:
        status: Overall health status (healthy/warning/critical)
        issues: List of identified problems
        timestamp: When the check was performed (UTC)
        metrics: Performance and health metrics
        resources: Resource utilization measurements

    Example:
        ```python
        result = HealthCheckResult(
            status="healthy",
            issues=[],
            timestamp=datetime.now(timezone.utc),
            metrics={"success_rate": 99.9, "error_rate": 0.1},
            resources={"cpu_usage": 45.2, "memory_usage": 78.5}
        )
        print(f"System status: {result.status}")
        print(f"Resource usage: {result['resources']}")
        ```
    """

    status: str
    issues: list[str]
    timestamp: datetime
    metrics: dict[str, Any]
    resources: dict[str, float]

    def __str__(self) -> str:
        """Convert the result to a string representation."""
        return str(self.status)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the health check result to a dictionary.

        Returns:
            Dictionary containing all health check data with ISO-formatted timestamp

        Example:
            ```python
            result = HealthCheckResult(...)
            data = result.to_dict()
            print(f"Check performed at: {data['timestamp']}")
            ```
        """
        return {
            "status": str(self.status),
            "issues": self.issues,
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics,
            "resources": self.resources,
        }

    def __getitem__(self, key: str) -> Any:
        """
        Make the object subscriptable by converting to dict first.

        Args:
            key: Dictionary key to access

        Returns:
            Value for the given key

        Example:
            ```python
            result = HealthCheckResult(...)
            status = result["status"]
            metrics = result["metrics"]
            ```
        """
        return self.to_dict()[key]
