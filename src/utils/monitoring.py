"""System monitoring and metrics collection."""

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, TypeVar

import numpy as np
import psutil
from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

# Constants for monitoring thresholds
MAX_LATENCY_MS = 500  # Maximum acceptable latency in milliseconds
MAX_CPU_PERCENT = 75  # Maximum acceptable CPU usage percentage

T = TypeVar("T")


@dataclass
class PerformanceMetrics:
    """Performance metrics for an operation.

    Attributes:
        latency_ms: Operation latency in milliseconds
        memory_mb: Memory usage in megabytes
        cpu_percent: CPU utilization percentage
        error_count: Number of errors encountered
        timestamp: UTC timestamp of measurement
        operation: Name of the operation being measured
    """

    latency_ms: float
    memory_mb: float
    cpu_percent: float
    error_count: int
    timestamp: str
    operation: str


class SystemMonitor:
    def __init__(
        self,
        log_path: str = "logs/system_metrics.log",
        max_history: int = 1000,
        metrics_interval: int = 60,
        export_format: str = "json",
    ):
        # Store configuration
        self.log_path = log_path
        self.max_history = max_history
        self.metrics_interval = metrics_interval
        self.export_format = export_format

        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        handler = logging.FileHandler(self.log_path)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        self.logger.addHandler(handler)

        # Initialize Prometheus metrics
        self.request_counter = Counter(
            "document_requests_total", "Total number of document requests"
        )
        self.processing_time = Histogram(
            "document_processing_seconds",
            "Time spent processing documents",
            buckets=(1, 5, 10, 30, 60, 120, 300, 600),
        )
        self.error_counter = Counter("processing_errors_total", "Total number of processing errors")
        self.memory_gauge = Gauge("memory_usage_bytes", "Current memory usage in bytes")
        self.cpu_gauge = Gauge("cpu_usage_percent", "Current CPU usage percentage")

        # Performance tracking
        self.performance_history: list[PerformanceMetrics] = []
        self.error_history: list[dict] = []

        # Resource monitoring
        self.process = psutil.Process()

    def _get_system_metrics(self) -> dict[str, float]:
        """Get current system resource usage."""
        return {
            "memory_mb": self.process.memory_info().rss / 1024 / 1024,
            "cpu_percent": self.process.cpu_percent(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def track_operation(self, operation_name: str):
        """Decorator to track operation performance."""

        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                error = None

                try:
                    result = func(*args, **kwargs)
                    try:
                        self.request_counter.inc()
                    except Exception as e:
                        self.logger.error(f"Error incrementing request counter: {e!s}")
                    return result
                except Exception as e:
                    error = e
                    try:
                        self.error_counter.inc()
                    except Exception as counter_error:
                        self.logger.error(f"Error incrementing error counter: {counter_error!s}")
                    self.logger.error(f"Error in {operation_name}: {e!s}", exc_info=True)
                    raise
                finally:
                    end_time = time.time()
                    duration = end_time - start_time

                    # Get system metrics
                    try:
                        metrics = self._get_system_metrics()
                    except Exception as e:
                        self.logger.error(f"Error getting system metrics: {e!s}")
                        metrics = {
                            "memory_mb": 0,
                            "cpu_percent": 0,
                            "timestamp": datetime.utcnow().isoformat(),
                        }

                    # Record performance metrics
                    perf_metrics = PerformanceMetrics(
                        latency_ms=duration * 1000,
                        memory_mb=metrics["memory_mb"],
                        cpu_percent=metrics["cpu_percent"],
                        error_count=1 if error else 0,
                        timestamp=metrics["timestamp"],
                        operation=operation_name,
                    )

                    # Maintain max history limit
                    self.performance_history.append(perf_metrics)
                    if len(self.performance_history) > self.max_history:
                        self.performance_history = self.performance_history[-self.max_history :]

                    # Update Prometheus metrics
                    try:
                        self._update_prometheus_metrics(
                            {
                                "duration": duration,
                                "memory_mb": metrics["memory_mb"],
                                "cpu_percent": metrics["cpu_percent"],
                            }
                        )
                    except Exception as e:
                        self.logger.error(f"Error updating Prometheus metrics: {e!s}")

                    # Log performance data
                    self.logger.info(
                        f"Operation: {operation_name}, "
                        f"Duration: {duration:.2f}s, "
                        f"Memory: {metrics['memory_mb']:.1f}MB, "
                        f"CPU: {metrics['cpu_percent']:.1f}%"
                    )

                    if error:
                        error_entry = {
                            "operation": operation_name,
                            "error": str(error),
                            "timestamp": metrics["timestamp"],
                        }
                        self.error_history.append(error_entry)
                        if len(self.error_history) > self.max_history:
                            self.error_history = self.error_history[-self.max_history :]

            return wrapper

        return decorator

    def get_performance_summary(self, hours: int = 24) -> dict[str, Any]:
        """Get performance summary for the last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        # Filter recent metrics
        recent_metrics = [
            m for m in self.performance_history if datetime.fromisoformat(m.timestamp) > cutoff
        ]

        if not recent_metrics:
            return {
                "status": "no_data",
                "period_hours": hours,
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Calculate statistics
        latencies = [m.latency_ms for m in recent_metrics]
        memory_usage = [m.memory_mb for m in recent_metrics]
        cpu_usage = [m.cpu_percent for m in recent_metrics]
        error_count = sum(m.error_count for m in recent_metrics)

        # Determine status based on metrics
        status = "healthy"
        if error_count > 0:
            status = "degraded"
        elif any(latency > MAX_LATENCY_MS for latency in latencies) or any(
            cpu > MAX_CPU_PERCENT for cpu in cpu_usage
        ):
            status = "warning"

        return {
            "status": status,
            "period_hours": hours,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "latency_ms": {
                    "min": np.min(latencies),
                    "max": np.max(latencies),
                    "mean": np.mean(latencies),
                    "std": np.std(latencies),
                    "p50": np.percentile(latencies, 50),
                    "p95": np.percentile(latencies, 95),
                    "p99": np.percentile(latencies, 99),
                },
                "memory_mb": {
                    "min": np.min(memory_usage),
                    "max": np.max(memory_usage),
                    "mean": np.mean(memory_usage),
                    "std": np.std(memory_usage),
                },
                "cpu_percent": {
                    "min": np.min(cpu_usage),
                    "max": np.max(cpu_usage),
                    "mean": np.mean(cpu_usage),
                    "std": np.std(cpu_usage),
                },
                "error_count": error_count,
            },
        }

    def _update_prometheus_metrics(self, metrics: dict[str, float]):
        """Update Prometheus metrics with current values."""
        try:
            self.processing_time.observe(metrics["duration"])
            self.memory_gauge.set(metrics["memory_mb"] * 1024 * 1024)
            self.cpu_gauge.set(metrics["cpu_percent"])
        except Exception as e:
            self.logger.error(f"Error updating Prometheus metrics: {e!s}")
            # Don't add to error history since this is an internal monitoring error

    def export_metrics(self, path: str):
        """Export all metrics to a JSON file."""
        try:
            metrics = {
                "performance": [
                    {
                        "latency_ms": m.latency_ms,
                        "memory_mb": m.memory_mb,
                        "cpu_percent": m.cpu_percent,
                        "error_count": m.error_count,
                        "timestamp": m.timestamp,
                        "operation": m.operation,
                    }
                    for m in self.performance_history
                ],
                "errors": self.error_history,
                "summary": self.get_performance_summary(),
            }

            with open(path, "w") as f:
                json.dump(metrics, f, indent=2)
        except OSError as e:
            self.logger.error(f"Failed to export metrics to {path}: {e!s}")
            raise
