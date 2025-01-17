# Alert Management System API Reference

## Overview

The alert management system provides a robust framework for handling system alerts, notifications, and monitoring. It supports multiple alert types, severity levels, and notification channels.

## Import Structure

```python
# Recommended imports (new style)
from src.core.monitoring.alerts.models.alert import Alert
from src.core.monitoring.alerts.models.config import AlertConfig
from src.core.monitoring.alerts.models.types import AlertSeverity, AlertType
from src.core.monitoring.alerts.lifecycle.manager import AlertLifecycleManager

# Legacy imports (deprecated, will be removed in 2.0.0)
from src.core.monitoring.alerts.models import Alert, AlertConfig, AlertSeverity, AlertType
```

## Core Components

### AlertLifecycleManager

The central class for managing alerts throughout their lifecycle.

```python
from src.core.monitoring.alerts.lifecycle.manager import AlertLifecycleManager
from src.core.monitoring.alerts.models.config import AlertConfig

# Initialize with configuration
config = AlertConfig(
    error_rate_threshold=0.1,
    memory_critical_threshold=90.0,
    alert_cooldown=300,
    email_config={
        "smtp_host": "smtp.example.com",
        "smtp_port": "587",
        "from_address": "alerts@example.com",
        "to_address": "admin@example.com",
    }
)

manager = AlertLifecycleManager(config)

# Create and send an alert
manager.send_alert(
    AlertType.RESOURCE,
    AlertSeverity.WARNING,
    "High memory usage detected",
    {"memory_usage": 85.5}
)

# Check system metrics and send alerts if needed
metrics = {"memory_usage": 85.0, "cpu_usage": 75.0, "error_rate": 0.05}
manager.check_and_alert(metrics)
```

### Alert Types and Severity

```python
from src.core.monitoring.alerts.models.types import AlertType, AlertSeverity

# Available alert types
AlertType.ERROR      # System errors and exceptions
AlertType.RESOURCE   # Resource utilization alerts
AlertType.SECURITY   # Security-related alerts
AlertType.PERFORMANCE # Performance degradation alerts

# Severity levels
AlertSeverity.INFO      # Informational alerts
AlertSeverity.WARNING   # Warning level alerts
AlertSeverity.CRITICAL  # Critical alerts (bypass cooldown)
```

### Alert Configuration

```python
from src.core.monitoring.alerts.models.config import AlertConfig

config = AlertConfig(
    # Thresholds
    error_rate_threshold=0.1,
    warning_rate_threshold=0.05,
    memory_critical_threshold=90.0,
    memory_warning_threshold=80.0,
    cpu_critical_threshold=90.0,
    cpu_warning_threshold=80.0,

    # Alert settings
    alert_cooldown=300,  # 5 minutes

    # Notification channels
    email_config={
        "smtp_host": "smtp.example.com",
        "smtp_port": "587",
        "from_address": "alerts@example.com",
        "to_address": "admin@example.com",
    },
    webhook_urls={
        "slack": "https://hooks.slack.com/services/...",
        "teams": "https://outlook.office.com/webhook/..."
    }
)
```

### Alert Model

```python
from src.core.monitoring.alerts.models.alert import Alert

# Create an alert
alert = Alert(
    alert_type=AlertType.ERROR,
    severity=AlertSeverity.CRITICAL,
    message="Database connection failed",
    metadata={"error_code": "DB_001", "attempts": 3}
)

# Work with alerts
alert.acknowledge()  # Mark as acknowledged
alert.resolve(notes="Connection restored after config update")
```

## Best Practices

1. **Alert Cooldown**: Non-critical alerts respect the cooldown period to prevent alert fatigue
2. **Critical Alerts**: Critical severity alerts bypass the cooldown period
3. **Metadata**: Include relevant context in alert metadata for better debugging
4. **Error Handling**: Always handle notification delivery failures gracefully
5. **Monitoring**: Use the check_and_alert method for automated system monitoring

## Migration Guide

When migrating from the legacy import structure:

1. Update imports to use specific paths:

   ```python
   # Old (deprecated)
   from src.core.monitoring.alerts.models import Alert, AlertConfig

   # New
   from src.core.monitoring.alerts.models.alert import Alert
   from src.core.monitoring.alerts.models.config import AlertConfig
   ```

2. Run tests with deprecation warnings enabled:

   ```python
   python -Wd -m pytest tests/
   ```

3. Update type hints if using them:

   ```python
   # Old
   from src.core.monitoring.alerts.models import Alert as AlertType

   # New
   from src.core.monitoring.alerts.models.alert import Alert as AlertType
   ```
