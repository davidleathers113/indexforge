"""Health check models and data structures.

This module provides the core models for system health monitoring, including
status enums and result classes for health checks.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class HealthStatus(Enum):
    """System health status levels."""

    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

    def __lt__(self, other: "HealthStatus") -> bool:
        """Enable comparison for max() operations."""
        order = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.WARNING: 1,
            HealthStatus.CRITICAL: 2,
        }
        return order[self] < order[other]


class ResourceMetrics:
    """System resource usage metrics.

    Attributes:
        memory_total: Total memory usage in MB
        memory_available: Available memory in MB
        memory_percent: Memory usage percentage
        cpu_percent: CPU usage percentage
        timestamp: When metrics were collected
    """

    def __init__(
        self,
        memory_total: int,
        memory_available: int,
        memory_percent: float,
        cpu_percent: float,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Initialize resource metrics.

        Args:
            memory_total: Total memory usage in MB
            memory_available: Available memory in MB
            memory_percent: Memory usage percentage
            cpu_percent: CPU usage percentage
            timestamp: When metrics were collected (defaults to current UTC time)
        """
        self.memory_total = memory_total
        self.memory_available = memory_available
        self.memory_percent = memory_percent
        self.cpu_percent = cpu_percent
        self.timestamp = timestamp or datetime.now(UTC)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to a dictionary.

        Returns:
            Dictionary representation of resource metrics
        """
        return {
            "memory_total": self.memory_total,
            "memory_available": self.memory_available,
            "memory_percent": self.memory_percent,
            "cpu_percent": self.cpu_percent,
            "timestamp": self.timestamp,
        }


class HealthCheckResult:
    """Result of a system health check.

    This class encapsulates the complete results of a health check, including
    overall status, resource metrics, and any issues found.

    Attributes:
        status: Overall health status
        metrics: System resource metrics
        issues: List of identified issues
        error_rate: Document processing error rate
        warning_rate: Document processing warning rate
        failed_docs_ratio: Ratio of failed document processing
        avg_processing_time: Average document processing time
        total_docs: Total number of documents processed
        timestamp: When health check was performed
    """

    def __init__(
        self,
        status: HealthStatus,
        metrics: ResourceMetrics,
        issues: Optional[List[str]] = None,
        error_rate: float = 0.0,
        warning_rate: float = 0.0,
        failed_docs_ratio: float = 0.0,
        avg_processing_time: float = 0.0,
        total_docs: int = 0,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Initialize health check result.

        Args:
            status: Overall health status
            metrics: System resource metrics
            issues: List of identified issues
            error_rate: Document processing error rate
            warning_rate: Document processing warning rate
            failed_docs_ratio: Ratio of failed document processing
            avg_processing_time: Average document processing time
            total_docs: Total number of documents processed
            timestamp: When health check was performed (defaults to current UTC time)
        """
        self.status = status
        self.metrics = metrics
        self.issues = issues or []
        self.error_rate = error_rate
        self.warning_rate = warning_rate
        self.failed_docs_ratio = failed_docs_ratio
        self.avg_processing_time = avg_processing_time
        self.total_docs = total_docs
        self.timestamp = timestamp or datetime.now(UTC)

    def to_dict(self) -> Dict[str, Any]:
        """Convert health check result to a dictionary.

        Returns:
            Dictionary representation of health check result
        """
        return {
            "status": self.status.value,
            "metrics": self.metrics.to_dict(),
            "issues": self.issues,
            "error_rate": self.error_rate,
            "warning_rate": self.warning_rate,
            "failed_docs_ratio": self.failed_docs_ratio,
            "avg_processing_time": self.avg_processing_time,
            "total_docs": self.total_docs,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HealthCheckResult":
        """Create a HealthCheckResult instance from a dictionary.

        Args:
            data: Dictionary containing health check data

        Returns:
            New HealthCheckResult instance
        """
        metrics_data = data["metrics"]
        metrics = ResourceMetrics(
            memory_total=metrics_data["memory_total"],
            memory_available=metrics_data["memory_available"],
            memory_percent=metrics_data["memory_percent"],
            cpu_percent=metrics_data["cpu_percent"],
            timestamp=metrics_data.get("timestamp"),
        )

        return cls(
            status=HealthStatus(data["status"]),
            metrics=metrics,
            issues=data.get("issues", []),
            error_rate=data.get("error_rate", 0.0),
            warning_rate=data.get("warning_rate", 0.0),
            failed_docs_ratio=data.get("failed_docs_ratio", 0.0),
            avg_processing_time=data.get("avg_processing_time", 0.0),
            total_docs=data.get("total_docs", 0),
            timestamp=data.get("timestamp"),
        )
