"""Status monitoring models for document processing.

This module provides the core models for tracking real-time status of document
processing operations, including system metrics and performance indicators.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, Optional


class SystemStatus(Enum):
    """Overall system status indicators."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    MAINTENANCE = "maintenance"


class StatusMetrics:
    """Real-time system metrics and performance indicators.

    Attributes:
        active_documents: Number of documents currently being processed
        queued_documents: Number of documents waiting to be processed
        completed_documents: Number of documents that finished processing
        error_count: Number of documents that encountered errors
        success_rate: Percentage of successful document processing
        average_processing_time: Average time to process a document (ms)
        system_load: Current system load percentage
        memory_usage: Current memory usage percentage
    """

    def __init__(
        self,
        active_documents: int = 0,
        queued_documents: int = 0,
        completed_documents: int = 0,
        error_count: int = 0,
        success_rate: float = 0.0,
        average_processing_time: Optional[float] = None,
        system_load: Optional[float] = None,
        memory_usage: Optional[float] = None,
    ) -> None:
        """Initialize status metrics.

        Args:
            active_documents: Number of documents being processed
            queued_documents: Number of documents in queue
            completed_documents: Number of completed documents
            error_count: Number of errors encountered
            success_rate: Processing success rate (0-100)
            average_processing_time: Average processing time in ms
            system_load: System load percentage (0-100)
            memory_usage: Memory usage percentage (0-100)
        """
        self.active_documents = active_documents
        self.queued_documents = queued_documents
        self.completed_documents = completed_documents
        self.error_count = error_count
        self.success_rate = success_rate
        self.average_processing_time = average_processing_time
        self.system_load = system_load
        self.memory_usage = memory_usage
        self.timestamp = datetime.now(UTC)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary format.

        Returns:
            Dictionary representation of metrics
        """
        return {
            "active_documents": self.active_documents,
            "queued_documents": self.queued_documents,
            "completed_documents": self.completed_documents,
            "error_count": self.error_count,
            "success_rate": self.success_rate,
            "average_processing_time": self.average_processing_time,
            "system_load": self.system_load,
            "memory_usage": self.memory_usage,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatusMetrics":
        """Create metrics from dictionary data.

        Args:
            data: Dictionary containing metrics data

        Returns:
            New StatusMetrics instance
        """
        metrics = cls(
            active_documents=data.get("active_documents", 0),
            queued_documents=data.get("queued_documents", 0),
            completed_documents=data.get("completed_documents", 0),
            error_count=data.get("error_count", 0),
            success_rate=data.get("success_rate", 0.0),
            average_processing_time=data.get("average_processing_time"),
            system_load=data.get("system_load"),
            memory_usage=data.get("memory_usage"),
        )
        if "timestamp" in data:
            metrics.timestamp = datetime.fromisoformat(data["timestamp"])
        return metrics


class SystemStatusReport:
    """Comprehensive system status report.

    This class combines current metrics with historical data and system health
    indicators to provide a complete view of system status.

    Attributes:
        status: Overall system status
        current_metrics: Current system metrics
        historical_metrics: Historical performance data
        warnings: List of active warnings
        errors: List of active errors
    """

    def __init__(
        self,
        status: SystemStatus,
        current_metrics: StatusMetrics,
        historical_metrics: Optional[Dict[str, Any]] = None,
        warnings: Optional[list[str]] = None,
        errors: Optional[list[str]] = None,
    ) -> None:
        """Initialize system status report.

        Args:
            status: Overall system status
            current_metrics: Current system metrics
            historical_metrics: Optional historical metrics
            warnings: Optional list of warnings
            errors: Optional list of errors
        """
        self.status = status
        self.current_metrics = current_metrics
        self.historical_metrics = historical_metrics or {}
        self.warnings = warnings or []
        self.errors = errors or []
        self.timestamp = datetime.now(UTC)

    def to_dict(self) -> Dict[str, Any]:
        """Convert status report to dictionary format.

        Returns:
            Dictionary representation of status report
        """
        return {
            "status": self.status.value,
            "current_metrics": self.current_metrics.to_dict(),
            "historical_metrics": self.historical_metrics,
            "warnings": self.warnings,
            "errors": self.errors,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemStatusReport":
        """Create status report from dictionary data.

        Args:
            data: Dictionary containing status report data

        Returns:
            New SystemStatusReport instance
        """
        return cls(
            status=SystemStatus(data["status"]),
            current_metrics=StatusMetrics.from_dict(data["current_metrics"]),
            historical_metrics=data.get("historical_metrics", {}),
            warnings=data.get("warnings", []),
            errors=data.get("errors", []),
        )
