"""Alert type and severity classifications.

This module defines the fundamental alert classification system, including
alert types and severity levels.
"""

from enum import Enum
from typing import Set


class AlertType(Enum):
    """Types of system alerts.

    Attributes:
        ERROR: System errors and exceptions
        RESOURCE: Resource usage and capacity alerts
        PERFORMANCE: Performance degradation and bottlenecks
        HEALTH: System health and status checks
        SECURITY: Security-related alerts and violations
        BACKUP: Backup and data persistence issues
        CONFIG: Configuration and settings problems
        INTEGRATION: External service integration issues
    """

    ERROR = "error"
    RESOURCE = "resource"
    PERFORMANCE = "performance"
    HEALTH = "health"
    SECURITY = "security"
    BACKUP = "backup"
    CONFIG = "config"
    INTEGRATION = "integration"

    @property
    def requires_immediate_action(self) -> bool:
        """Check if this alert type typically requires immediate action."""
        return self in self.immediate_action_types()

    @classmethod
    def immediate_action_types(cls) -> Set["AlertType"]:
        """Get set of alert types requiring immediate action."""
        return {
            cls.ERROR,
            cls.SECURITY,
            cls.RESOURCE,
        }


class AlertSeverity(Enum):
    """Severity levels for alerts.

    Attributes:
        CRITICAL: Immediate attention required
        WARNING: Potential issues requiring monitoring
        INFO: Informational alerts for tracking
    """

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

    @property
    def notification_priority(self) -> int:
        """Get the notification priority level (higher is more urgent)."""
        return self.priority_levels()[self]

    @classmethod
    def priority_levels(cls) -> dict["AlertSeverity", int]:
        """Get mapping of severity levels to priority values."""
        return {
            cls.CRITICAL: 3,
            cls.WARNING: 2,
            cls.INFO: 1,
        }
