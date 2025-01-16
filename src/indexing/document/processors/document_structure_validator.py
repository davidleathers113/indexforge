"""Document structure validation processor.

This module provides document validation functionality, ensuring documents
meet required structure, content, and metadata requirements before processing.
"""

import time
from typing import Any

from src.api.monitoring.collectors.document_metrics import DocumentMetrics
from src.api.monitoring.tracing import DocumentTracer
from src.indexing.document.processors.document_processor_base import BaseDocumentProcessor


class DocumentStructureValidator(BaseDocumentProcessor):
    """Validates document structure, content, and metadata."""

    def __init__(
        self,
        metrics: DocumentMetrics,
        tracer: DocumentTracer,
        required_fields: set[str] | None = None,
        content_min_length: int = 10,
        max_metadata_keys: int = 20,
    ):
        """Initialize document validator.

        Args:
            metrics: Document metrics collector
            tracer: Document tracer
            required_fields: Set of required document fields
            content_min_length: Minimum content length
            max_metadata_keys: Maximum number of metadata keys
        """
        super().__init__(metrics, tracer, "document_validator")
        self.required_fields = required_fields or {"content", "metadata"}
        self.content_min_length = content_min_length
        self.max_metadata_keys = max_metadata_keys

    def process(self, document: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Validate document structure and content.

        Args:
            document: Document to validate
            **kwargs: Additional validation parameters

        Returns:
            Validated document

        Raises:
            ValueError: If document fails validation
        """
        start_time = time.time()
        document_id = self._get_document_id(document)

        try:
            self._record_processing_start(document_id)

            with self.tracer.start_validation(
                document_id=document_id, validation_type="structure"
            ) as span:
                # Basic structure validation
                self._validate_document_structure(document)
                span.set_attribute("validation.structure", "complete")
                self.metrics.record_validation_check("structure", "pass")

                # Required fields validation
                self._validate_required_fields(document)
                span.set_attribute("validation.required_fields", "complete")
                self.metrics.record_validation_check("required_fields", "pass")

                # Content validation
                self._validate_content(document)
                span.set_attribute("validation.content", "complete")
                self.metrics.record_validation_check("content", "pass")

                # Metadata validation
                self._validate_metadata(document)
                span.set_attribute("validation.metadata", "complete")
                self.metrics.record_validation_check("metadata", "pass")

                # Record document size
                size = self._get_document_size(document)
                span.set_attribute("document.size", size)
                self.metrics.record_document_size(size, "validated")

                duration = time.time() - start_time
                span.set_attribute("processing.duration", duration)
                self._record_processing_success(document_id, duration)

                return document

        except Exception as e:
            duration = time.time() - start_time
            self._record_processing_error(document_id, e)
            raise

    def _validate_required_fields(self, document: dict[str, Any]) -> None:
        """Validate presence of required fields.

        Args:
            document: Document to validate

        Raises:
            ValueError: If required fields are missing
        """
        missing_fields = self.required_fields - set(document.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    def _validate_content(self, document: dict[str, Any]) -> None:
        """Validate document content.

        Args:
            document: Document to validate

        Raises:
            ValueError: If content validation fails
        """
        content = document.get("content", "")
        if not isinstance(content, str):
            raise ValueError("Content must be a string")

        if len(content.strip()) < self.content_min_length:
            raise ValueError(
                f"Content length ({len(content.strip())}) below minimum required "
                f"({self.content_min_length})"
            )

    def _validate_metadata(self, document: dict[str, Any]) -> None:
        """Validate document metadata.

        Args:
            document: Document to validate

        Raises:
            ValueError: If metadata validation fails
        """
        metadata = document.get("metadata", {})
        if not isinstance(metadata, dict):
            raise ValueError("Metadata must be a dictionary")

        if len(metadata) > self.max_metadata_keys:
            raise ValueError(
                f"Number of metadata keys ({len(metadata)}) exceeds maximum allowed "
                f"({self.max_metadata_keys})"
            )

        # Validate metadata values are primitive types
        invalid_values = []
        for key, value in metadata.items():
            if not isinstance(value, (str, int, float, bool, type(None))):
                invalid_values.append(key)

        if invalid_values:
            raise ValueError(
                f"Invalid metadata value types for keys: {', '.join(invalid_values)}. "
                "Only primitive types allowed (string, number, boolean, null)"
            )
