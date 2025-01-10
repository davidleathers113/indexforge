"""Document processing metrics collection.

This module provides metrics collection specifically for document processing
operations, including processing duration, error rates, and size distributions.
"""

from prometheus_client import Counter, Histogram


class DocumentMetrics:
    """Document processing metrics collector."""

    def __init__(self, namespace: str = "document"):
        """Initialize document metrics collectors.

        Args:
            namespace: Metrics namespace for Prometheus
        """
        # Processing duration by stage
        self.processing_duration = Histogram(
            f"{namespace}_processing_duration_seconds",
            "Document processing duration by stage",
            ["stage", "status"],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 7.5, 10.0),
        )

        # Error counts by type and stage
        self.processing_errors = Counter(
            f"{namespace}_processing_errors_total",
            "Document processing errors by type",
            ["error_type", "stage"],
        )

        # Document size distribution
        self.document_size = Histogram(
            f"{namespace}_size_bytes",
            "Document size distribution",
            ["type"],  # raw, processed, enriched
            buckets=(1000, 10000, 100000, 1000000),
        )

        # Batch processing metrics
        self.batch_size = Histogram(
            f"{namespace}_batch_size",
            "Document batch size distribution",
            buckets=(1, 5, 10, 50, 100, 500),
        )

        # Processing success/failure counts
        self.processing_total = Counter(
            f"{namespace}_processing_total",
            "Total number of documents processed",
            ["stage", "status"],
        )

        # Cache metrics
        self.cache_operations = Counter(
            f"{namespace}_cache_operations_total",
            "Cache operation counts",
            ["operation", "status"],  # hit, miss, error
        )

        # Embedding metrics
        self.embedding_generation = Histogram(
            f"{namespace}_embedding_generation_seconds",
            "Time taken to generate embeddings",
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 7.5, 10.0),
        )

        # Validation metrics
        self.validation_checks = Counter(
            f"{namespace}_validation_checks_total",
            "Number of validation checks performed",
            ["check_type", "status"],  # structure, content, schema
        )

    def record_processing_duration(
        self, stage: str, duration: float, status: str = "success"
    ) -> None:
        """Record document processing duration.

        Args:
            stage: Processing stage name
            duration: Duration in seconds
            status: Operation status (success/error)
        """
        self.processing_duration.labels(stage=stage, status=status).observe(duration)
        self.processing_total.labels(stage=stage, status=status).inc()

    def record_error(self, error_type: str, stage: str) -> None:
        """Record processing error.

        Args:
            error_type: Type of error encountered
            stage: Stage where error occurred
        """
        self.processing_errors.labels(error_type=error_type, stage=stage).inc()
        self.processing_total.labels(stage=stage, status="error").inc()

    def record_document_size(self, size: int, doc_type: str = "raw") -> None:
        """Record document size.

        Args:
            size: Document size in bytes
            doc_type: Document type (raw/processed/enriched)
        """
        self.document_size.labels(type=doc_type).observe(size)

    def record_batch_size(self, size: int) -> None:
        """Record batch processing size.

        Args:
            size: Number of documents in batch
        """
        self.batch_size.observe(size)

    def record_cache_operation(self, operation: str, status: str) -> None:
        """Record cache operation result.

        Args:
            operation: Type of cache operation
            status: Operation status (hit/miss/error)
        """
        self.cache_operations.labels(operation=operation, status=status).inc()

    def record_embedding_generation(self, duration: float) -> None:
        """Record embedding generation time.

        Args:
            duration: Time taken to generate embeddings in seconds
        """
        self.embedding_generation.observe(duration)

    def record_validation_check(self, check_type: str, status: str) -> None:
        """Record validation check result.

        Args:
            check_type: Type of validation check
            status: Check status (pass/fail)
        """
        self.validation_checks.labels(check_type=check_type, status=status).inc()
