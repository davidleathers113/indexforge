"""Alert configuration model.

This module defines the configuration data structure for alert settings.
"""

from dataclasses import dataclass, field
from typing import ClassVar

from src.core.monitoring.alerts.validators import ConfigValidator


@dataclass
class AlertConfig:
    """Configuration for alert thresholds and notification settings.

    This class holds configuration parameters for determining when to trigger
    alerts and how to send notifications. It includes thresholds for various
    metrics and settings for notification channels.

    Attributes:
        error_rate_threshold: Maximum acceptable error rate (0-1)
        warning_rate_threshold: Warning level error rate (0-1)
        memory_critical_threshold: Critical memory usage percent
        memory_warning_threshold: Warning memory usage percent
        cpu_critical_threshold: Critical CPU usage percent
        cpu_warning_threshold: Warning CPU usage percent
        disk_critical_threshold: Critical disk usage percent
        disk_warning_threshold: Warning disk usage percent
        processing_time_critical: Critical processing time (seconds)
        processing_time_warning: Warning processing time (seconds)
        alert_cooldown: Seconds between similar alerts
        email_config: Email notification settings
        webhook_urls: Webhook notification endpoints
        max_retries: Maximum notification delivery attempts
        retry_delay: Delay between retry attempts (seconds)
    """

    # Thresholds
    error_rate_threshold: float = 0.1
    warning_rate_threshold: float = 0.05
    memory_critical_threshold: float = 90.0
    memory_warning_threshold: float = 80.0
    cpu_critical_threshold: float = 90.0
    cpu_warning_threshold: float = 80.0
    disk_critical_threshold: float = 90.0
    disk_warning_threshold: float = 80.0
    processing_time_critical: float = 600.0  # 10 minutes
    processing_time_warning: float = 300.0  # 5 minutes

    # Alert settings
    alert_cooldown: int = 300  # 5 minutes between similar alerts
    max_retries: int = 3
    retry_delay: int = 60

    # Notification channels
    email_config: dict[str, str] | None = None
    webhook_urls: dict[str, str] = field(default_factory=dict)

    # Class-level constants
    MAX_THRESHOLD: ClassVar[float] = 100.0
    MIN_THRESHOLD: ClassVar[float] = 0.0
    MIN_COOLDOWN: ClassVar[int] = 60

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        ConfigValidator.validate_thresholds(self)
        ConfigValidator.validate_timing(
            self.alert_cooldown,
            self.max_retries,
            self.retry_delay,
        )
