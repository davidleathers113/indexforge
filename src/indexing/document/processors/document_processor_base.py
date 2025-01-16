"""Base document processor implementation.

This module provides the base processor class with common functionality
for document processing operations, including metrics and tracing integration.
"""

from abc import ABC, abstractmethod
from typing import Any

from src.api.monitoring.collectors.document_metrics import DocumentMetrics
from src.api.monitoring.tracing import DocumentTracer


class BaseDocumentProcessor(ABC):
    """Base class for document processors."""

    def __init__(self, metrics: DocumentMetrics, tracer: DocumentTracer, processor_name: str):
        """Initialize base document processor.

        Args:
            metrics: Document metrics collector
            tracer: Document tracer for distributed tracing
            processor_name: Name of the processor for metrics/tracing
        """
        self.metrics = metrics
        self.tracer = tracer
        self.processor_name = processor_name

    @abstractmethod
    def process(self, document: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Process a document.

        Args:
            document: Document to process
            **kwargs: Additional processing arguments

        Returns:
            Processed document

        Raises:
            NotImplementedError: Must be implemented by derived classes
        """
        raise NotImplementedError

    def _record_processing_start(
        self, document_id: str, attributes: dict[str, Any] | None = None
    ) -> None:
        """Record start of document processing.

        Args:
            document_id: Document identifier
            attributes: Additional attributes for tracing
        """
        if attributes is None:
            attributes = {}

        self.metrics.processing_total.labels(stage=self.processor_name, status="started").inc()

    def _record_processing_success(
        self, document_id: str, duration: float, attributes: dict[str, Any] | None = None
    ) -> None:
        """Record successful document processing.

        Args:
            document_id: Document identifier
            duration: Processing duration in seconds
            attributes: Additional attributes for tracing
        """
        if attributes is None:
            attributes = {}

        self.metrics.record_processing_duration(
            stage=self.processor_name, duration=duration, status="success"
        )

    def _record_processing_error(
        self, document_id: str, error: Exception, attributes: dict[str, Any] | None = None
    ) -> None:
        """Record document processing error.

        Args:
            document_id: Document identifier
            error: Exception that occurred
            attributes: Additional attributes for tracing
        """
        if attributes is None:
            attributes = {}

        error_type = error.__class__.__name__
        self.metrics.record_error(error_type=error_type, stage=self.processor_name)

    def _get_document_id(self, document: dict[str, Any]) -> str:
        """Extract document identifier.

        Args:
            document: Document to process

        Returns:
            Document identifier

        Raises:
            ValueError: If document ID is missing
        """
        doc_id = document.get("id") or document.get("document_id")
        if not doc_id:
            raise ValueError("Document must have 'id' or 'document_id' field")
        return str(doc_id)

    def _get_document_size(self, document: dict[str, Any]) -> int:
        """Calculate document size.

        Args:
            document: Document to measure

        Returns:
            Document size in bytes
        """
        # Simple size estimation using string representation
        return len(str(document).encode("utf-8"))

    def _validate_document_structure(self, document: dict[str, Any]) -> None:
        """Validate basic document structure.

        Args:
            document: Document to validate

        Raises:
            ValueError: If document structure is invalid
        """
        if not isinstance(document, dict):
            raise ValueError("Document must be a dictionary")

        if not document:
            raise ValueError("Document cannot be empty")
