"""
Manages document lineage tracking and operations.

This module contains the DocumentLineageManager class, which provides methods for:
- Adding documents to lineage tracking
- Recording transformations and derivations
- Fetching lineage and transformation history
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Union

from .enums import LogLevel, ProcessingStatus, TransformationType
from .health_check import perform_health_check
from .metrics import get_aggregated_metrics
from .models import DocumentLineage, HealthCheckResult, LogEntry, ProcessingStep, Transformation
from .utils import load_json, save_json
from .validation import validate_circular_derivations, validate_lineage_relationships

logger = logging.getLogger(__name__)


class DocumentLineageManager:
    """Manages document lineage tracking and operations."""

    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize the document lineage manager.

        Args:
            storage_dir: Optional directory for storing lineage data
        """
        self.storage_dir = Path(storage_dir) if storage_dir else Path(__file__).parent / "lineage"
        self.lineage_data: Dict[str, DocumentLineage] = {}
        self._load_lineage_data()

    def _get_storage_path(self) -> Path:
        """Get path for lineage data storage."""
        return self.storage_dir / "document_lineage.json"

    def _load_lineage_data(self) -> None:
        """Load existing lineage data from storage."""
        try:
            storage_path = self._get_storage_path()
            data = load_json(storage_path)
            for doc_id, lineage in data.items():
                self.lineage_data[doc_id] = DocumentLineage(
                    doc_id=doc_id,
                    origin_id=lineage.get("origin_id"),
                    origin_source=lineage.get("origin_source"),
                    origin_type=lineage.get("origin_type"),
                    derived_from=lineage.get("derived_from"),
                    derived_documents=lineage.get("derived_documents", []),
                    transformations=[
                        Transformation(
                            transform_type=TransformationType(t["transform_type"]),
                            timestamp=datetime.fromisoformat(t["timestamp"]),
                            description=t.get("description", ""),
                            parameters=t.get("parameters", {}),
                            metadata=t.get("metadata", {}),
                        )
                        for t in lineage.get("transformations", [])
                    ],
                    processing_steps=[
                        ProcessingStep(
                            step_name=p["step_name"],
                            status=ProcessingStatus(p["status"]),
                            timestamp=datetime.fromisoformat(p["timestamp"]),
                            details=p.get("details", {}),
                        )
                        for p in lineage.get("processing_steps", [])
                    ],
                    error_logs=[
                        LogEntry(
                            log_level=LogLevel(log_entry["log_level"]),
                            message=log_entry["message"],
                            timestamp=datetime.fromisoformat(log_entry["timestamp"]),
                            metadata=log_entry.get("metadata", {}),
                        )
                        for log_entry in lineage.get("error_logs", [])
                    ],
                    performance_metrics=lineage.get("performance_metrics", {}),
                    metadata=lineage.get("metadata", {}),
                    created_at=datetime.fromisoformat(lineage["created_at"]),
                    last_modified=datetime.fromisoformat(lineage["last_modified"]),
                )
        except Exception as e:
            logger.error(f"Error loading lineage data: {e}")
            self.lineage_data = {}

    def _save_lineage_data(self) -> None:
        """Save current lineage data to storage."""
        try:
            data = {
                doc_id: {
                    "origin_id": lineage.origin_id,
                    "origin_source": lineage.origin_source,
                    "origin_type": lineage.origin_type,
                    "derived_from": lineage.derived_from,
                    "derived_documents": lineage.derived_documents,
                    "transformations": [
                        {
                            "transform_type": t.transform_type.value,
                            "timestamp": t.timestamp.isoformat(),
                            "description": t.description,
                            "parameters": t.parameters,
                            "metadata": t.metadata,
                        }
                        for t in lineage.transformations
                    ],
                    "processing_steps": [
                        {
                            "step_name": p.step_name,
                            "status": p.status.value,
                            "timestamp": p.timestamp.isoformat(),
                            "details": p.details,
                        }
                        for p in lineage.processing_steps
                    ],
                    "error_logs": [
                        {
                            "log_level": log_entry.log_level.value,
                            "message": log_entry.message,
                            "timestamp": log_entry.timestamp.isoformat(),
                            "metadata": log_entry.metadata,
                        }
                        for log_entry in lineage.error_logs
                    ],
                    "performance_metrics": lineage.performance_metrics,
                    "metadata": lineage.metadata,
                    "created_at": lineage.created_at.isoformat(),
                    "last_modified": lineage.last_modified.isoformat(),
                }
                for doc_id, lineage in self.lineage_data.items()
            }

            save_json(self._get_storage_path(), data)
        except Exception as e:
            logger.error(f"Error saving lineage data: {e}")
            raise

    def add_document(
        self,
        doc_id: str,
        origin_id: Optional[str] = None,
        origin_source: Optional[str] = None,
        origin_type: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Add a new document to lineage tracking.

        Args:
            doc_id: Unique identifier for the document
            origin_id: Optional ID of the original source
            origin_source: Optional source system/location
            origin_type: Optional type of the source
            metadata: Optional metadata about the document

        Raises:
            ValueError: If document already exists
        """
        if doc_id in self.lineage_data:
            raise ValueError(f"Document {doc_id} already exists in lineage tracking")

        self.lineage_data[doc_id] = DocumentLineage(
            doc_id=doc_id,
            origin_id=origin_id,
            origin_source=origin_source,
            origin_type=origin_type,
            metadata=metadata or {},
        )
        self._save_lineage_data()

    def record_transformation(
        self,
        doc_id: str,
        transform_type: Union[TransformationType, str],
        description: str = "",
        parameters: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Record a transformation applied to a document.

        Args:
            doc_id: ID of the document
            transform_type: Type of transformation
            description: Optional description of the transformation
            parameters: Optional parameters used in the transformation
            metadata: Optional metadata about the transformation

        Raises:
            ValueError: If document doesn't exist
        """
        if doc_id not in self.lineage_data:
            raise ValueError(f"Document {doc_id} not found in lineage tracking")

        if isinstance(transform_type, str):
            transform_type = TransformationType(transform_type)

        transformation = Transformation(
            transform_type=transform_type,
            description=description,
            parameters=parameters or {},
            metadata=metadata or {},
        )

        lineage = self.lineage_data[doc_id]
        lineage.transformations.append(transformation)
        lineage.last_modified = datetime.now(timezone.utc)
        self._save_lineage_data()

    def add_derivation(
        self,
        parent_id: str,
        derived_id: str,
        transform_type: Optional[Union[TransformationType, str]] = None,
        description: str = "",
        parameters: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Link a derived document to its parent.

        Args:
            parent_id: ID of the parent document
            derived_id: ID of the derived document
            transform_type: Optional type of transformation that created the derivation
            description: Optional description of the derivation
            parameters: Optional parameters used in the derivation
            metadata: Optional metadata about the derivation

        Raises:
            ValueError: If parent document doesn't exist
        """
        if parent_id not in self.lineage_data:
            raise ValueError(f"Parent document {parent_id} not found in lineage tracking")

        # Add derived document if it doesn't exist
        if derived_id not in self.lineage_data:
            self.add_document(
                doc_id=derived_id,
                origin_id=self.lineage_data[parent_id].origin_id,
                origin_source=self.lineage_data[parent_id].origin_source,
                origin_type=self.lineage_data[parent_id].origin_type,
            )

        # Update parent's derived documents
        parent = self.lineage_data[parent_id]
        if derived_id not in parent.derived_documents:
            parent.derived_documents.append(derived_id)
            parent.last_modified = datetime.now(timezone.utc)

        # Update derived document's parent reference
        derived = self.lineage_data[derived_id]
        derived.derived_from = parent_id
        derived.last_modified = datetime.now(timezone.utc)

        # Record transformation if provided
        if transform_type:
            self.record_transformation(
                derived_id,
                transform_type,
                description=description,
                parameters=parameters,
                metadata=metadata,
            )

        self._save_lineage_data()

    def get_lineage(self, doc_id: str) -> Optional[DocumentLineage]:
        """Get lineage information for a document.

        Args:
            doc_id: ID of the document

        Returns:
            DocumentLineage object if found, None otherwise
        """
        return self.lineage_data.get(doc_id)

    def get_transformation_history(
        self, doc_id: str, transform_type: Optional[Union[TransformationType, str]] = None
    ) -> List[Transformation]:
        """Get transformation history for a document.

        Args:
            doc_id: ID of the document
            transform_type: Optional filter by transformation type

        Returns:
            List of transformations
        """
        if doc_id not in self.lineage_data:
            return []

        transformations = self.lineage_data[doc_id].transformations
        if transform_type:
            if isinstance(transform_type, str):
                transform_type = TransformationType(transform_type)
            transformations = [t for t in transformations if t.transform_type == transform_type]

        return transformations

    def get_derivation_chain(self, doc_id: str, max_depth: int = 10) -> Dict[str, List[str]]:
        """Get the derivation chain for a document.

        Args:
            doc_id: ID of the document
            max_depth: Maximum depth to traverse in the derivation chain

        Returns:
            Dictionary mapping each document to its derived documents
        """
        if doc_id not in self.lineage_data or max_depth <= 0:
            return {}

        chain = {doc_id: self.lineage_data[doc_id].derived_documents}
        for derived_id in self.lineage_data[doc_id].derived_documents:
            chain.update(self.get_derivation_chain(derived_id, max_depth - 1))

        return chain

    def validate_lineage(self) -> List[str]:
        """Validate the integrity of document lineage.

        Returns:
            List of validation error messages
        """
        errors = []
        errors.extend(validate_lineage_relationships(self.lineage_data))
        errors.extend(validate_circular_derivations(self.lineage_data))
        return errors

    def health_check(self, thresholds: Optional[Dict[str, float]] = None) -> HealthCheckResult:
        """Perform a health check of the system.

        Args:
            thresholds: Optional custom thresholds for health checks

        Returns:
            HealthCheckResult object containing status and metrics
        """
        metrics = get_aggregated_metrics(self.lineage_data)
        return perform_health_check(metrics, thresholds)

    def log_error_or_warning(
        self,
        doc_id: str,
        log_level: Union[LogLevel, str],
        message: str,
        details: Optional[Dict] = None,
    ) -> None:
        """Log an error or warning for a document.

        Args:
            doc_id: ID of the document to update
            log_level: Log level (error/warning)
            message: Error/warning message
            details: Optional additional details

        Example:
            ```python
            # Log an error
            manager.log_error_or_warning(
                doc_id="doc123",
                log_level=LogLevel.ERROR,
                message="Failed to process images",
                details={"failed_pages": [1, 3]}
            )
            ```
        """
        if doc_id not in self.lineage_data:
            raise ValueError(f"Document {doc_id} not found")

        if isinstance(log_level, str):
            log_level = LogLevel(log_level.lower())

        log_entry = LogEntry(
            log_level=log_level,
            message=message,
            metadata=details or {},
        )

        lineage = self.lineage_data[doc_id]
        lineage.error_logs.append(log_entry)
        lineage.last_modified = datetime.now(timezone.utc)
        self._save_lineage_data()

    def get_error_logs(
        self,
        doc_id: str,
        log_level: Optional[LogLevel] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[LogEntry]:
        """Get error logs for a document with optional filters.

        Args:
            doc_id: ID of the document
            log_level: Optional filter by log level (error/warning)
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            List of LogEntry objects matching the filters

        Example:
            ```python
            # Get all error logs
            logs = manager.get_error_logs("doc123")

            # Get only error level logs
            error_logs = manager.get_error_logs("doc123", log_level=LogLevel.ERROR)

            # Get recent logs
            recent_logs = manager.get_error_logs(
                "doc123",
                start_time=datetime.now() - timedelta(hours=1)
            )
            ```
        """
        if doc_id not in self.lineage_data:
            return []

        logs = self.lineage_data[doc_id].error_logs

        # Filter by log level if specified
        if log_level:
            logs = [log for log in logs if log.log_level == log_level]

        # Filter by time range if specified
        if start_time:
            logs = [log for log in logs if log.timestamp >= start_time]
        if end_time:
            logs = [log for log in logs if log.timestamp <= end_time]

        return logs
