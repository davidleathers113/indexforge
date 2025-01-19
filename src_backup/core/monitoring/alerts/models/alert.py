"""Alert model.

This module defines the core Alert data structure.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from src.core.monitoring.alerts.validators import AlertValidator

from .types import AlertSeverity, AlertType


@dataclass
class Alert:
    """Represents a system alert.

    This class encapsulates all information about a specific alert,
    including its type, severity, message, and associated metadata.
    It automatically generates a unique alert ID based on its properties.

    Attributes:
        alert_type: Type of the alert
        severity: Severity level
        message: Alert message
        timestamp: When the alert was created
        metadata: Additional alert context
        alert_id: Unique identifier (auto-generated)
        acknowledged: Whether the alert has been acknowledged
        resolved: Whether the alert has been resolved
        resolution_time: When the alert was resolved
        resolution_notes: Notes about how the alert was resolved
    """

    alert_type: AlertType
    severity: AlertSeverity
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)
    alert_id: str = field(init=False)
    acknowledged: bool = field(default=False)
    resolved: bool = field(default=False)
    resolution_time: datetime | None = None
    resolution_notes: str | None = None

    def __post_init__(self) -> None:
        """Generate a unique alert ID and validate fields.

        The ID is created by combining the alert type, severity, and timestamp
        to ensure uniqueness while maintaining readability.
        """
        self.alert_id = (
            f"{self.alert_type.value}_{self.severity.value}_{self.timestamp.timestamp()}"
        )
        self._validate()

    def _validate(self) -> None:
        """Validate alert fields using AlertValidator."""
        AlertValidator.validate_message(self.message)
        AlertValidator.validate_resolution(
            self.resolved,
            self.resolution_time,
            self.timestamp,
        )

    def acknowledge(self) -> None:
        """Mark the alert as acknowledged."""
        self.acknowledged = True

    def resolve(self, notes: str | None = None) -> None:
        """Mark the alert as resolved.

        Args:
            notes: Optional notes about how the alert was resolved
        """
        self.resolved = True
        self.resolution_time = datetime.now(UTC)
        if notes:
            self.resolution_notes = notes
        self._validate()

    @property
    def resolution_duration(self) -> timedelta | None:
        """Calculate how long it took to resolve the alert."""
        if not self.resolved or not self.resolution_time:
            return None
        return self.resolution_time - self.timestamp

    @property
    def requires_immediate_action(self) -> bool:
        """Check if this alert requires immediate action."""
        return self.severity == AlertSeverity.CRITICAL or self.alert_type.requires_immediate_action
