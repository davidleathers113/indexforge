"""Distributed tracing configuration for document processing.

This module provides OpenTelemetry tracing setup and utilities for document
processing operations, enabling end-to-end visibility of document flows.
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode


class DocumentTracer:
    """Document processing tracer."""

    def __init__(self, service_name: str = "document-processor"):
        """Initialize document tracer.

        Args:
            service_name: Name of the service for tracing
        """
        self.tracer = trace.get_tracer(service_name)

    @contextmanager
    def start_processing(
        self, document_id: str, stage: str, attributes: dict[str, Any] | None = None
    ) -> Generator[Span, None, None]:
        """Start a processing span for document operations.

        Args:
            document_id: Unique identifier of the document
            stage: Processing stage name
            attributes: Additional span attributes

        Yields:
            Active span for the processing operation
        """
        if attributes is None:
            attributes = {}

        # Add standard attributes
        span_attributes = {"document.id": document_id, "processing.stage": stage, **attributes}

        with self.tracer.start_as_current_span(
            name=f"document.{stage}", attributes=span_attributes
        ) as span:
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    @contextmanager
    def start_validation(
        self, document_id: str, validation_type: str, attributes: dict[str, Any] | None = None
    ) -> Generator[Span, None, None]:
        """Start a validation span for document checks.

        Args:
            document_id: Unique identifier of the document
            validation_type: Type of validation being performed
            attributes: Additional span attributes

        Yields:
            Active span for the validation operation
        """
        if attributes is None:
            attributes = {}

        span_attributes = {
            "document.id": document_id,
            "validation.type": validation_type,
            **attributes,
        }

        with self.tracer.start_as_current_span(
            name=f"document.validate.{validation_type}", attributes=span_attributes
        ) as span:
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    @contextmanager
    def start_enrichment(
        self, document_id: str, enrichment_type: str, attributes: dict[str, Any] | None = None
    ) -> Generator[Span, None, None]:
        """Start an enrichment span for document enhancement.

        Args:
            document_id: Unique identifier of the document
            enrichment_type: Type of enrichment being performed
            attributes: Additional span attributes

        Yields:
            Active span for the enrichment operation
        """
        if attributes is None:
            attributes = {}

        span_attributes = {
            "document.id": document_id,
            "enrichment.type": enrichment_type,
            **attributes,
        }

        with self.tracer.start_as_current_span(
            name=f"document.enrich.{enrichment_type}", attributes=span_attributes
        ) as span:
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    @contextmanager
    def start_batch_processing(
        self,
        batch_id: str,
        operation: str,
        batch_size: int,
        attributes: dict[str, Any] | None = None,
    ) -> Generator[Span, None, None]:
        """Start a batch processing span.

        Args:
            batch_id: Unique identifier for the batch
            operation: Type of batch operation
            batch_size: Number of documents in batch
            attributes: Additional span attributes

        Yields:
            Active span for the batch operation
        """
        if attributes is None:
            attributes = {}

        span_attributes = {
            "batch.id": batch_id,
            "batch.operation": operation,
            "batch.size": batch_size,
            **attributes,
        }

        with self.tracer.start_as_current_span(
            name=f"document.batch.{operation}", attributes=span_attributes
        ) as span:
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
