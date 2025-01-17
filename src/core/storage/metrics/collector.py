"""Storage metrics collector.

This module provides functionality for collecting and managing storage metrics,
including operation tracking, system resource monitoring, and performance analysis.

Key Features:
    - Operation tracking with timing
    - System resource monitoring
    - Performance metrics calculation
    - Thread-safe metric collection
    - Configurable collection windows
"""

from __future__ import annotations

import logging
import threading
from collections import deque
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Deque

import psutil

from .models import OperationMetrics, PerformanceMetrics, StorageMetrics

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collector for storage metrics."""

    def __init__(
        self,
        storage_path: Path,
        max_history: int = 1000,
        window_seconds: int = 300,
    ) -> None:
        """Initialize metrics collector.

        Args:
            storage_path: Path to storage directory
            max_history: Maximum number of operation metrics to keep
            window_seconds: Time window for performance metrics in seconds
        """
        self.storage_path = storage_path
        self.window_seconds = window_seconds
        self._operation_metrics: Deque[OperationMetrics] = deque(maxlen=max_history)
        self._lock = threading.Lock()

    def record_operation(
        self,
        operation_type: str,
        document_id: str,
        duration_ms: float,
        success: bool = True,
        error_message: str | None = None,
    ) -> None:
        """Record a storage operation.

        Args:
            operation_type: Type of operation (create/update/delete)
            document_id: ID of document involved
            duration_ms: Operation duration in milliseconds
            success: Whether operation succeeded
            error_message: Error message if operation failed
        """
        metric = OperationMetrics(
            operation_type=operation_type,
            document_id=document_id,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
        )

        with self._lock:
            self._operation_metrics.append(metric)

    def get_storage_metrics(self) -> StorageMetrics:
        """Get current storage metrics.

        Returns:
            Current storage metrics
        """
        try:
            usage = psutil.disk_usage(str(self.storage_path))
            total_docs = len(list(self.storage_path.glob("*.json")))

            return StorageMetrics(
                total_space_bytes=usage.total,
                used_space_bytes=usage.used,
                free_space_bytes=usage.free,
                total_documents=total_docs,
            )
        except Exception as e:
            logger.error("Failed to collect storage metrics: %s", e)
            raise

    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get performance metrics for recent operations.

        Returns:
            Performance metrics for configured time window
        """
        with self._lock:
            # Filter metrics within time window
            cutoff = datetime.now(UTC) - timedelta(seconds=self.window_seconds)
            recent_metrics = [m for m in self._operation_metrics if m.timestamp >= cutoff]

            if not recent_metrics:
                return PerformanceMetrics(
                    avg_latency_ms=0.0,
                    throughput_ops=0.0,
                    error_rate=0.0,
                    window_seconds=self.window_seconds,
                )

            # Calculate metrics
            total_ops = len(recent_metrics)
            failed_ops = len([m for m in recent_metrics if not m.success])
            avg_latency = sum(m.duration_ms for m in recent_metrics) / total_ops
            throughput = total_ops / self.window_seconds
            error_rate = failed_ops / total_ops if total_ops > 0 else 0.0

            return PerformanceMetrics(
                avg_latency_ms=avg_latency,
                throughput_ops=throughput,
                error_rate=error_rate,
                window_seconds=self.window_seconds,
            )

    def clear_metrics(self) -> None:
        """Clear all collected metrics."""
        with self._lock:
            self._operation_metrics.clear()
