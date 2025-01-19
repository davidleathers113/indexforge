"""
System health check results.

This module provides the HealthCheckResult model for tracking system health status,
including performance metrics, resource utilization, and identified issues.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from src.core.tracking.enums import HealthStatus


@dataclass
class HealthCheckResult:
    """
    Result of a system health check.

    This class contains the results of a system health check, including overall
    status, any issues found, and various metrics about system performance.

    Attributes:
        status: Overall health status (healthy/warning/critical)
        issues: List of identified problems
        timestamp: When the check was performed (UTC)
        metrics: Performance and health metrics
        resources: Resource utilization measurements

    Example:
        ```python
        result = HealthCheckResult(
            status=HealthStatus.HEALTHY,
            issues=[],
            metrics={"success_rate": 99.9, "error_rate": 0.1},
            resources={"cpu_usage": 45.2, "memory_usage": 78.5}
        )
        print(f"System status: {result.status}")
        print(f"Resource usage: {result.resources}")
        ```
    """

    status: HealthStatus
    issues: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metrics: dict[str, Any] = field(default_factory=dict)
    resources: dict[str, float] = field(default_factory=dict)

    def __str__(self) -> str:
        """Convert the result to a string representation."""
        return str(self.status)

    def to_dict(self) -> dict[str, Any]:
        """Convert the health check result to a dictionary."""
        return {
            "status": self.status.value,
            "issues": self.issues,
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics,
            "resources": self.resources,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HealthCheckResult":
        """Create a HealthCheckResult instance from a dictionary."""
        data = data.copy()  # Create a copy to avoid modifying the input
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if isinstance(data.get("status"), str):
            data["status"] = HealthStatus(data["status"])
        return cls(**data)
