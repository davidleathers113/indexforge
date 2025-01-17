"""Monitoring utilities for reference system performance and health.

This module provides tools for monitoring cache performance, reference health,
and system metrics.
"""

import logging
import time
from dataclasses import dataclass
from uuid import UUID

from .reference_cache import ReferenceCache
from .reference_classifier import ReferenceClassifier
from .references import ReferenceManager, ReferenceType

logger = logging.getLogger(__name__)


@dataclass
class ReferenceHealthMetrics:
    """Health metrics for reference system."""

    total_references: int = 0
    orphaned_references: int = 0
    circular_references: int = 0
    invalid_references: int = 0
    bidirectional_mismatches: int = 0


@dataclass
class PerformanceMetrics:
    """Performance metrics for reference operations."""

    operation_count: int = 0
    total_time_ms: float = 0
    avg_time_ms: float = 0.0
    max_time_ms: float = 0.0
    min_time_ms: float = float("inf")


class ReferenceMonitor:
    """Monitor for reference system health and performance."""

    def __init__(
        self,
        ref_manager: ReferenceManager,
        cache: ReferenceCache | None = None,
        classifier: ReferenceClassifier | None = None,
    ):
        """Initialize reference monitor.

        Args:
            ref_manager: Reference manager to monitor
            cache: Optional reference cache to monitor
            classifier: Optional reference classifier to monitor
        """
        self.ref_manager = ref_manager
        self.cache = cache
        self.classifier = classifier
        self.performance_metrics: dict[str, PerformanceMetrics] = {}

    def check_reference_health(self) -> ReferenceHealthMetrics:
        """Check health of reference system.

        Returns:
            Health metrics for reference system
        """
        metrics = ReferenceHealthMetrics()
        metrics.total_references = len(self.ref_manager._references)

        # Track processed references to detect cycles
        processed: set[UUID] = set()
        component: set[UUID] = set()

        def check_circular_references(chunk_id: UUID, path: set[UUID]) -> None:
            """Check for circular references starting from chunk.

            Args:
                chunk_id: ID of chunk to check
                path: Set of chunk IDs in current path
            """
            if chunk_id in path:
                metrics.circular_references += 1
                return

            if chunk_id in processed:
                return

            path.add(chunk_id)
            component.add(chunk_id)

            # Check forward references
            for ref in self.ref_manager.get_chunk_references(chunk_id).values():
                if ref.target_id in self.ref_manager._chunks:
                    check_circular_references(ref.target_id, path)

            path.remove(chunk_id)

        # Check all chunks for circular references
        for chunk_id in self.ref_manager._chunks:
            if chunk_id not in processed:
                component.clear()
                check_circular_references(chunk_id, set())
                processed.update(component)

        # Check for orphaned and invalid references
        for (source_id, target_id), ref in self.ref_manager._references.items():
            if source_id not in self.ref_manager._chunks:
                metrics.orphaned_references += 1
            if target_id not in self.ref_manager._chunks:
                metrics.orphaned_references += 1

            # Check bidirectional consistency
            if ref.bidirectional:
                reverse_key = (target_id, source_id)
                if reverse_key not in self.ref_manager._references:
                    metrics.bidirectional_mismatches += 1
                else:
                    reverse_ref = self.ref_manager._references[reverse_key]
                    if not reverse_ref.bidirectional:
                        metrics.bidirectional_mismatches += 1

            # Validate reference metadata
            try:
                self._validate_reference_metadata(ref)
            except ValueError:
                metrics.invalid_references += 1

        return metrics

    def _validate_reference_metadata(self, ref) -> None:
        """Validate reference metadata.

        Args:
            ref: Reference to validate

        Raises:
            ValueError: If reference metadata is invalid
        """
        if ref.ref_type == ReferenceType.SIMILAR:
            if "similarity_score" not in ref.metadata:
                raise ValueError("Missing similarity score for similar reference")
            score = ref.metadata["similarity_score"]
            if not isinstance(score, int | float) or not 0 <= score <= 1:
                raise ValueError("Invalid similarity score")

        if ref.ref_type == ReferenceType.CITATION:
            if "citation_type" not in ref.metadata:
                raise ValueError("Missing citation type for citation reference")

    def get_cache_metrics(self) -> dict | None:
        """Get cache performance metrics.

        Returns:
            Cache metrics if cache is available, None otherwise
        """
        if not self.cache:
            return None

        stats = self.cache.get_stats()
        return {
            "hit_rate": stats.hit_rate,
            "total_requests": stats.total_requests,
            "hits": stats.hits,
            "misses": stats.misses,
            "invalidations": stats.invalidations,
            "cache_size": len(self.cache.reference_cache),
            "forward_index_size": sum(len(v) for v in self.cache.forward_index.values()),
            "reverse_index_size": sum(len(v) for v in self.cache.reverse_index.values()),
        }

    def record_operation_time(self, operation: str, time_ms: float) -> None:
        """Record time taken for an operation.

        Args:
            operation: Name of operation
            time_ms: Time taken in milliseconds
        """
        if operation not in self.performance_metrics:
            self.performance_metrics[operation] = PerformanceMetrics()

        metrics = self.performance_metrics[operation]
        metrics.operation_count += 1
        metrics.total_time_ms += time_ms
        metrics.avg_time_ms = metrics.total_time_ms / metrics.operation_count
        metrics.max_time_ms = max(metrics.max_time_ms, time_ms)
        metrics.min_time_ms = min(metrics.min_time_ms, time_ms)

    def get_performance_metrics(self) -> dict[str, PerformanceMetrics]:
        """Get performance metrics for all operations.

        Returns:
            Dictionary mapping operation names to performance metrics
        """
        return self.performance_metrics

    def log_metrics(self, log_level: int = logging.INFO) -> None:
        """Log all metrics.

        Args:
            log_level: Logging level to use
        """
        # Log health metrics
        health = self.check_reference_health()
        logger.log(
            log_level,
            "Reference Health Metrics: total=%d, orphaned=%d, circular=%d, "
            "invalid=%d, bidirectional_mismatches=%d",
            health.total_references,
            health.orphaned_references,
            health.circular_references,
            health.invalid_references,
            health.bidirectional_mismatches,
        )

        # Log cache metrics if available
        if self.cache:
            cache_metrics = self.get_cache_metrics()
            logger.log(
                log_level,
                "Cache Metrics: hit_rate=%.2f%%, requests=%d, hits=%d, misses=%d, "
                "invalidations=%d, size=%d",
                cache_metrics["hit_rate"],
                cache_metrics["total_requests"],
                cache_metrics["hits"],
                cache_metrics["misses"],
                cache_metrics["invalidations"],
                cache_metrics["cache_size"],
            )

        # Log performance metrics
        for operation, metrics in self.performance_metrics.items():
            logger.log(
                log_level,
                "Performance Metrics for %s: count=%d, avg=%.2fms, min=%.2fms, " "max=%.2fms",
                operation,
                metrics.operation_count,
                metrics.avg_time_ms,
                metrics.min_time_ms,
                metrics.max_time_ms,
            )


def time_operation(monitor: ReferenceMonitor, operation: str):
    """Decorator to time operations and record metrics.

    Args:
        monitor: Reference monitor to record metrics
        operation: Name of operation to time
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            monitor.record_operation_time(operation, (end - start) * 1000)
            return result

        return wrapper

    return decorator
