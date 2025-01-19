"""Service metrics collection and monitoring.

This module provides a comprehensive metrics collection system for monitoring
service performance, resource usage, and operational health.
"""

from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import psutil


@dataclass
class OperationMetrics:
    """Metrics for a single operation."""

    operation_name: str
    start_time: datetime
    end_time: datetime | None = None
    duration: float | None = None
    success: bool = True
    error_type: str | None = None
    error_message: str | None = None
    memory_usage: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ServiceMetricsCollector:
    """Collects and analyzes service metrics."""

    def __init__(
        self,
        service_name: str,
        max_history: int = 1000,
        memory_threshold_mb: float = 500,
    ) -> None:
        """Initialize metrics collector.

        Args:
            service_name: Name of the service being monitored
            max_history: Maximum number of operations to keep in history
            memory_threshold_mb: Memory usage threshold in MB
        """
        self.service_name = service_name
        self.max_history = max_history
        self.memory_threshold_mb = memory_threshold_mb

        # Metrics storage
        self.operations: list[OperationMetrics] = []
        self.error_counts: dict[str, int] = defaultdict(int)
        self.operation_counts: dict[str, int] = defaultdict(int)
        self.slow_operations: set[str] = set()
        self._current_operation: OperationMetrics | None = None

    @contextmanager
    def measure_operation(
        self,
        operation_name: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Measure operation performance.

        Args:
            operation_name: Name of the operation
            metadata: Optional operation metadata
        """
        metrics = OperationMetrics(
            operation_name=operation_name,
            start_time=datetime.now(),
            metadata=metadata or {},
        )
        self._current_operation = metrics

        try:
            # Record initial memory
            metrics.memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
            yield
            metrics.success = True
        except Exception as e:
            metrics.success = False
            metrics.error_type = type(e).__name__
            metrics.error_message = str(e)
            self.error_counts[operation_name] += 1
            raise
        finally:
            # Record metrics
            metrics.end_time = datetime.now()
            metrics.duration = (metrics.end_time - metrics.start_time).total_seconds()

            # Update operation counts
            self.operation_counts[operation_name] += 1

            # Check for slow operations (>100ms)
            if metrics.duration > 0.1:
                self.slow_operations.add(operation_name)

            # Store operation history
            self.operations.append(metrics)
            if len(self.operations) > self.max_history:
                self.operations.pop(0)

            self._current_operation = None

    def get_current_metrics(self) -> dict[str, Any]:
        """Get current service metrics.

        Returns:
            Dict[str, Any]: Current metrics
        """
        if not self.operations:
            return {}

        recent_ops = self.operations[-min(100, len(self.operations)) :]
        durations = [op.duration for op in recent_ops if op.duration is not None]
        memory_usage = [op.memory_usage for op in recent_ops if op.memory_usage is not None]

        return {
            "service_name": self.service_name,
            "total_operations": sum(self.operation_counts.values()),
            "error_rate": sum(self.error_counts.values())
            / max(sum(self.operation_counts.values()), 1),
            "avg_duration": sum(durations) / max(len(durations), 1) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "avg_memory_mb": sum(memory_usage) / max(len(memory_usage), 1) if memory_usage else 0,
            "max_memory_mb": max(memory_usage) if memory_usage else 0,
            "operation_counts": dict(self.operation_counts),
            "error_counts": dict(self.error_counts),
            "slow_operations": list(self.slow_operations),
        }

    def get_operation_metrics(
        self,
        operation_name: str,
        time_window: timedelta | None = None,
    ) -> dict[str, Any]:
        """Get metrics for a specific operation.

        Args:
            operation_name: Name of the operation
            time_window: Optional time window to filter metrics

        Returns:
            Dict[str, Any]: Operation metrics
        """
        if not self.operations:
            return {}

        # Filter operations
        filtered_ops = [
            op
            for op in self.operations
            if op.operation_name == operation_name
            and (not time_window or datetime.now() - op.start_time <= time_window)
        ]

        if not filtered_ops:
            return {}

        durations = [op.duration for op in filtered_ops if op.duration is not None]
        memory_usage = [op.memory_usage for op in filtered_ops if op.memory_usage is not None]

        return {
            "operation_name": operation_name,
            "total_calls": self.operation_counts[operation_name],
            "error_rate": self.error_counts[operation_name]
            / max(self.operation_counts[operation_name], 1),
            "avg_duration": sum(durations) / max(len(durations), 1) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "avg_memory_mb": sum(memory_usage) / max(len(memory_usage), 1) if memory_usage else 0,
            "max_memory_mb": max(memory_usage) if memory_usage else 0,
            "success_rate": len([op for op in filtered_ops if op.success]) / len(filtered_ops),
        }

    def check_health(self) -> dict[str, Any]:
        """Check service health based on metrics.

        Returns:
            Dict[str, Any]: Health check results
        """
        metrics = self.get_current_metrics()
        if not metrics:
            return {"status": "unknown", "checks": {}}

        checks = {
            "memory_usage": {
                "status": (
                    "healthy"
                    if metrics.get("max_memory_mb", 0) < self.memory_threshold_mb
                    else "warning"
                ),
                "value": metrics.get("max_memory_mb", 0),
                "threshold": self.memory_threshold_mb,
            },
            "error_rate": {
                "status": "healthy" if metrics.get("error_rate", 0) < 0.05 else "warning",
                "value": metrics.get("error_rate", 0),
                "threshold": 0.05,
            },
            "performance": {
                "status": "healthy" if len(metrics.get("slow_operations", [])) == 0 else "warning",
                "slow_operations": metrics.get("slow_operations", []),
            },
        }

        # Determine overall status
        if any(check["status"] == "warning" for check in checks.values()):
            status = "warning"
        else:
            status = "healthy"

        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "checks": checks,
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self.operations.clear()
        self.error_counts.clear()
        self.operation_counts.clear()
        self.slow_operations.clear()
        self._current_operation = None
