"""Alert management system.

This package provides comprehensive alert management functionality for monitoring
system health, resource usage, and application status. It supports configurable
thresholds, multiple notification channels, and alert lifecycle management.

Example:
    ```python
    from src.core.monitoring.alerts import AlertConfig, AlertLifecycleManager
    from src.core.monitoring.alerts import AlertType, AlertSeverity

    # Create alert configuration
    config = AlertConfig(
        memory_critical_threshold=90.0,
        memory_warning_threshold=80.0,
        email_config={
            "smtp_host": "smtp.example.com",
            "smtp_port": "587",
            "from_address": "alerts@example.com",
            "to_address": "admin@example.com",
        }
    )

    # Initialize alert manager
    manager = AlertLifecycleManager(config)

    # Create and process alert
    alert = manager.create_alert(
        alert_type=AlertType.RESOURCE,
        severity=AlertSeverity.WARNING,
        message="High memory usage detected",
        metadata={"memory_usage": 85.5}
    )
    ```
"""

from .lifecycle import AlertLifecycleManager
from .models import Alert, AlertConfig, AlertSeverity, AlertType
from .validators import AlertValidator, ConfigValidator


__all__ = [
    # Core models
    "Alert",
    "AlertConfig",
    "AlertType",
    "AlertSeverity",
    # Validators
    "AlertValidator",
    "ConfigValidator",
    # Lifecycle management
    "AlertLifecycleManager",
]
