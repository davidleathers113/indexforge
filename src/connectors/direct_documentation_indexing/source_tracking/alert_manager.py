"""
System alert and notification management for document processing.

This module provides a comprehensive alert management system for monitoring
and notifying about various system events, resource usage, and processing
issues. It supports multiple notification channels including email and
webhooks, with configurable thresholds and cooldown periods.

Key Features:
    - Multiple alert types (error, resource, performance, health)
    - Configurable severity levels
    - Email notifications
    - Webhook integrations
    - Alert cooldown management
    - Threshold-based triggering
    - Alert history tracking

Example:
    ```python
    # Initialize alert manager with custom config
    manager = AlertManager(config_path="/path/to/config.json")

    # Send a critical alert
    manager.send_alert(
        alert_type=AlertType.ERROR,
        severity=AlertSeverity.CRITICAL,
        message="Database connection failed",
        metadata={"error": "Connection timeout"}
    )

    # Send a resource warning
    manager.send_alert(
        alert_type=AlertType.RESOURCE,
        severity=AlertSeverity.WARNING,
        message="High memory usage detected",
        metadata={"usage_percent": 85}
    )
    ```
"""

import json
import logging
import smtplib
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """
    Types of system alerts.

    Attributes:
        ERROR: System errors and exceptions
        RESOURCE: Resource usage and capacity alerts
        PERFORMANCE: Performance degradation and bottlenecks
        HEALTH: System health and status checks

    Example:
        ```python
        # Use alert types
        alert_type = AlertType.ERROR
        if alert_type == AlertType.RESOURCE:
            print("Resource alert")
        ```
    """

    ERROR = "error"
    RESOURCE = "resource"
    PERFORMANCE = "performance"
    HEALTH = "health"


class AlertSeverity(Enum):
    """
    Severity levels for alerts.

    Attributes:
        CRITICAL: Immediate attention required
        WARNING: Potential issues requiring monitoring
        INFO: Informational alerts for tracking

    Example:
        ```python
        # Check alert severity
        if alert.severity == AlertSeverity.CRITICAL:
            notify_admin()
        elif alert.severity == AlertSeverity.WARNING:
            log_warning()
        ```
    """

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class AlertConfig:
    """
    Configuration for alert thresholds and notification settings.

    This class holds configuration parameters for determining when to trigger
    alerts and how to send notifications. It includes thresholds for various
    metrics and settings for notification channels.

    Attributes:
        error_rate_threshold (float): Maximum acceptable error rate (0-1)
        warning_rate_threshold (float): Warning level error rate (0-1)
        memory_critical_threshold (float): Critical memory usage percent
        memory_warning_threshold (float): Warning memory usage percent
        cpu_critical_threshold (float): Critical CPU usage percent
        cpu_warning_threshold (float): Warning CPU usage percent
        disk_critical_threshold (float): Critical disk usage percent
        disk_warning_threshold (float): Warning disk usage percent
        processing_time_critical (float): Critical processing time (seconds)
        processing_time_warning (float): Warning processing time (seconds)
        alert_cooldown (int): Seconds between similar alerts
        email_config (Optional[Dict[str, str]]): Email notification settings
        webhook_urls (Dict[str, str]): Webhook notification endpoints

    Example:
        ```python
        # Create custom configuration
        config = AlertConfig(
            error_rate_threshold=0.05,
            memory_critical_threshold=95.0,
            alert_cooldown=600,
            email_config={
                "smtp_host": "smtp.example.com",
                "smtp_port": "587",
                "from_address": "alerts@example.com",
                "to_address": "admin@example.com"
            }
        )
        ```
    """

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
    alert_cooldown: int = 300  # 5 minutes between similar alerts
    email_config: Optional[Dict[str, str]] = None
    webhook_urls: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """
    Represents a system alert.

    This class encapsulates all information about a specific alert,
    including its type, severity, message, and associated metadata.
    It automatically generates a unique alert ID based on its properties.

    Attributes:
        alert_type (AlertType): Type of the alert
        severity (AlertSeverity): Severity level
        message (str): Alert message
        timestamp (datetime): When the alert was created
        metadata (Dict[str, Any]): Additional alert context
        alert_id (str): Unique identifier (auto-generated)

    Example:
        ```python
        # Create an alert
        alert = Alert(
            alert_type=AlertType.PERFORMANCE,
            severity=AlertSeverity.WARNING,
            message="High latency detected",
            metadata={
                "latency_ms": 500,
                "threshold_ms": 200
            }
        )
        print(f"Alert ID: {alert.alert_id}")
        ```
    """

    alert_type: AlertType
    severity: AlertSeverity
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    alert_id: str = field(init=False)

    def __post_init__(self):
        """
        Generate a unique alert ID.

        The ID is created by combining the alert type, severity, and timestamp
        to ensure uniqueness while maintaining readability.
        """
        self.alert_id = (
            f"{self.alert_type.value}_{self.severity.value}_{self.timestamp.timestamp()}"
        )


class AlertManager:
    """
    Manages system alerts and notifications.

    This class handles the creation, tracking, and distribution of system
    alerts through various notification channels. It supports email and
    webhook notifications with configurable thresholds and cooldown periods
    to prevent alert fatigue.

    Attributes:
        config (AlertConfig): Alert configuration settings
        recent_alerts (Dict[str, datetime]): Recently sent alerts
        alert_history (List[Alert]): Historical record of alerts

    Example:
        ```python
        # Initialize manager with custom config
        config = AlertConfig(
            error_rate_threshold=0.05,
            alert_cooldown=600
        )
        manager = AlertManager(alert_config=config)

        # Send alerts
        manager.send_alert(
            alert_type=AlertType.ERROR,
            severity=AlertSeverity.CRITICAL,
            message="Database connection lost",
            metadata={"error": "Timeout"}
        )

        # Check health and trigger alerts
        health_data = get_system_health()
        manager.check_and_alert(health_data)
        ```
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        alert_config: Optional[AlertConfig] = None,
    ):
        """
        Initialize the AlertManager.

        This method sets up the alert manager with either a configuration
        loaded from a file or a provided AlertConfig instance. If neither
        is provided, default configuration values are used.

        Args:
            config_path: Path to JSON configuration file
            alert_config: Pre-configured AlertConfig instance

        Example:
            ```python
            # Initialize with config file
            manager = AlertManager(config_path="/path/to/config.json")

            # Initialize with config object
            config = AlertConfig(alert_cooldown=600)
            manager = AlertManager(alert_config=config)

            # Initialize with defaults
            manager = AlertManager()
            ```
        """
        logger.debug("Initializing AlertManager with config: %s", alert_config)
        self.config = alert_config or self._load_config(config_path)
        self.recent_alerts: Dict[str, datetime] = {}
        self.alert_history: List[Alert] = []
        logger.debug("AlertManager initialized successfully")

    def _load_config(self, config_path: Optional[str]) -> AlertConfig:
        """
        Load alert configuration from file or use defaults.

        This method attempts to load configuration from a JSON file if provided.
        If the file doesn't exist or has errors, it falls back to default values.

        Args:
            config_path: Path to configuration file

        Returns:
            AlertConfig instance with loaded or default settings

        Example:
            ```python
            # Load from file
            config = manager._load_config("/path/to/config.json")

            # Load defaults if file doesn't exist
            config = manager._load_config(None)
            ```

        Note:
            The configuration file should be a JSON file with keys matching
            AlertConfig attributes. For example:
            {
                "error_rate_threshold": 0.1,
                "memory_critical_threshold": 90.0,
                "alert_cooldown": 300,
                "email_config": {
                    "smtp_host": "smtp.example.com",
                    "smtp_port": "587"
                }
            }
        """
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, "r") as f:
                    config_data = json.load(f)
                return AlertConfig(**config_data)
            except Exception as e:
                logger.error(f"Error loading alert configuration: {e}")

        return AlertConfig()

    def send_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send an alert through configured channels.

        This method creates and sends an alert through appropriate notification
        channels based on its severity. Critical alerts are sent via both email
        and webhooks, while warnings are sent only via webhooks. The method also
        handles alert cooldown to prevent alert fatigue.

        Args:
            alert_type: Type of alert (ERROR, RESOURCE, etc.)
            severity: Alert severity (CRITICAL, WARNING, INFO)
            message: Alert message text
            metadata: Optional dictionary of additional context

        Returns:
            True if alert was sent successfully, False if suppressed or failed

        Example:
            ```python
            # Send critical error alert
            success = manager.send_alert(
                alert_type=AlertType.ERROR,
                severity=AlertSeverity.CRITICAL,
                message="Database connection failed",
                metadata={
                    "error": "Connection timeout",
                    "retry_count": 3
                }
            )

            # Send resource warning
            success = manager.send_alert(
                alert_type=AlertType.RESOURCE,
                severity=AlertSeverity.WARNING,
                message="High memory usage",
                metadata={"usage_percent": 85}
            )
            ```

        Note:
            Alerts may be suppressed if a similar alert was sent within
            the cooldown period. Critical alerts are sent through all
            available channels, while lower severity alerts may use
            fewer channels.
        """
        logger.debug(
            "Sending alert - Type: %s, Severity: %s, Message: %s, Metadata: %s",
            alert_type.value,
            severity.value,
            message,
            metadata,
        )

        alert = Alert(
            alert_type=alert_type,
            severity=severity,
            message=message,
            metadata=metadata or {},
        )
        logger.debug("Created alert object with ID: %s", alert.alert_id)

        if not self._should_send_alert(alert):
            logger.debug("Alert suppressed due to cooldown: %s", alert.alert_id)
            return False

        logger.debug("Storing alert in history: %s", alert.alert_id)
        self.alert_history.append(alert)
        self.recent_alerts[alert.alert_id] = alert.timestamp

        success = True
        if alert.severity == AlertSeverity.CRITICAL:
            logger.debug("Sending critical alert via email and webhooks")
            email_success = self._send_email_alert(alert)
            webhook_success = self._send_webhook_alerts(alert)
            success = email_success and webhook_success
            logger.debug(
                "Critical alert sent - Email: %s, Webhook: %s",
                email_success,
                webhook_success,
            )
        elif alert.severity == AlertSeverity.WARNING:
            logger.debug("Sending warning alert via webhooks only")
            success = self._send_webhook_alerts(alert)
            logger.debug("Warning alert sent via webhook: %s", success)

        logger.debug("Alert sending completed with success: %s", success)
        return success

    def _should_send_alert(self, alert: Alert) -> bool:
        """
        Check if an alert should be sent based on cooldown period.

        This method implements the alert cooldown logic to prevent alert
        fatigue. It checks if a similar alert has been sent recently and
        cleans up old alerts from the tracking system.

        Args:
            alert: Alert to check

        Returns:
            True if the alert should be sent, False if it should be suppressed

        Example:
            ```python
            alert = Alert(
                alert_type=AlertType.ERROR,
                severity=AlertSeverity.CRITICAL,
                message="Service unavailable"
            )
            if manager._should_send_alert(alert):
                send_notification(alert)
            ```

        Note:
            Similar alerts are determined by matching alert type and severity.
            The cooldown period is configured in AlertConfig.alert_cooldown.
        """
        logger.debug("Checking alert cooldown for ID: %s", alert.alert_id)
        now = datetime.now(timezone.utc)
        cooldown = timedelta(seconds=self.config.alert_cooldown)
        logger.debug("Current cooldown period: %s seconds", cooldown.total_seconds())

        for alert_id, timestamp in list(self.recent_alerts.items()):
            age = now - timestamp
            logger.debug("Alert %s age: %s seconds", alert_id, age.total_seconds())

            if age > cooldown:
                logger.debug("Removing expired alert from tracking: %s", alert_id)
                del self.recent_alerts[alert_id]
                continue

            if (
                alert_id.startswith(f"{alert.alert_type.value}_{alert.severity.value}")
                and age < cooldown
            ):
                logger.debug(
                    "Similar alert %s still in cooldown (age: %s seconds)",
                    alert_id,
                    age.total_seconds(),
                )
                return False

        logger.debug("No similar alerts in cooldown period")
        return True

    def _send_email_alert(self, alert: Alert) -> bool:
        """
        Send alert via email.

        This method sends an alert through email using the configured SMTP
        settings. It formats the alert into a readable email message and
        handles the SMTP connection and authentication.

        Args:
            alert: Alert to send

        Returns:
            True if email was sent successfully, False otherwise

        Example:
            ```python
            alert = Alert(
                alert_type=AlertType.ERROR,
                severity=AlertSeverity.CRITICAL,
                message="System failure",
                metadata={"error": "Out of memory"}
            )
            success = manager._send_email_alert(alert)
            ```

        Note:
            Requires email configuration in AlertConfig.email_config with:
            - smtp_host: SMTP server hostname
            - smtp_port: SMTP server port
            - from_address: Sender email address
            - to_address: Recipient email address
            - smtp_user: Optional SMTP authentication username
            - smtp_password: Optional SMTP authentication password
        """
        if not self.config.email_config:
            logger.debug("Email configuration not available")
            return False

        try:
            logger.debug(f"Preparing email alert: {alert.alert_id}")
            msg = MIMEText(
                f"Alert: {alert.message}\n\n"
                f"Type: {alert.alert_type.value}\n"
                f"Severity: {alert.severity.value}\n"
                f"Time: {alert.timestamp.isoformat()}\n"
                f"Metadata: {json.dumps(alert.metadata, indent=2)}"
            )

            msg["Subject"] = (
                f"[{alert.severity.value.upper()}] System Alert: {alert.alert_type.value}"
            )
            msg["From"] = self.config.email_config["from_address"]
            msg["To"] = self.config.email_config["to_address"]

            logger.debug(
                f"Connecting to SMTP server: {self.config.email_config['smtp_host']}:{self.config.email_config['smtp_port']}"
            )
            with smtplib.SMTP(
                self.config.email_config["smtp_host"],
                int(self.config.email_config["smtp_port"]),
            ) as server:
                if self.config.email_config.get("smtp_user"):
                    logger.debug("Authenticating with SMTP server")
                    server.login(
                        self.config.email_config["smtp_user"],
                        self.config.email_config["smtp_password"],
                    )
                logger.debug("Sending email")
                server.send_message(msg)

            logger.debug("Email alert sent successfully")
            return True
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
            return False

    def _send_webhook_alerts(self, alert: Alert) -> bool:
        """
        Send alert to configured webhooks.

        This method sends an alert to all configured webhook endpoints.
        It formats the alert as a JSON payload and sends it via HTTP POST
        requests to each webhook URL.

        Args:
            alert: Alert to send

        Returns:
            True if all webhooks were notified successfully, False otherwise

        Example:
            ```python
            alert = Alert(
                alert_type=AlertType.PERFORMANCE,
                severity=AlertSeverity.WARNING,
                message="High latency detected",
                metadata={"latency_ms": 500}
            )
            success = manager._send_webhook_alerts(alert)
            ```

        Note:
            Webhook URLs should be configured in AlertConfig.webhook_urls
            as a dictionary mapping webhook names to their URLs. The alert
            is sent as a JSON payload with the following structure:
            {
                "type": alert_type,
                "severity": severity,
                "message": message,
                "timestamp": timestamp,
                "metadata": metadata
            }
        """
        if not self.config.webhook_urls:
            logger.debug("No webhook URLs configured")
            return False

        success = True
        payload = {
            "type": alert.alert_type.value,
            "severity": alert.severity.value,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
            "metadata": alert.metadata,
        }

        for webhook_name, webhook_url in self.config.webhook_urls.items():
            try:
                logger.debug(f"Sending webhook alert to {webhook_name}: {webhook_url}")
                response = requests.post(webhook_url, json=payload, timeout=5)
                response.raise_for_status()
                logger.debug(f"Webhook alert sent successfully to {webhook_name}")
            except Exception as e:
                logger.error(f"Error sending webhook alert to {webhook_name}: {e}")
                success = False

        return success

    def check_and_alert(self, health_check_result: Dict[str, Any]) -> None:
        """Check health status and send alerts if needed.

        Args:
            health_check_result: Result from health check
        """
        logger.debug("Processing health check result: %s", health_check_result)

        status = health_check_result["status"]
        issues = health_check_result["issues"]
        metrics = health_check_result["metrics"]
        resources = health_check_result["resources"]

        logger.debug("System status: %s, Issues: %s", status, issues)
        logger.debug("Resources: %s", resources)
        logger.debug("Metrics: %s", metrics)

        # System health status check
        if status == "critical":
            logger.debug("System health is CRITICAL")
            self.send_alert(
                alert_type=AlertType.HEALTH,
                severity=AlertSeverity.CRITICAL,
                message=f"System health critical: {', '.join(issues)}",
                metadata={"metrics": metrics, "resources": resources},
            )
        elif status == "warning":
            logger.debug("System health is WARNING")
            self.send_alert(
                alert_type=AlertType.HEALTH,
                severity=AlertSeverity.WARNING,
                message=f"System health warning: {', '.join(issues)}",
                metadata={"metrics": metrics, "resources": resources},
            )

        # Memory usage check
        memory_percent = resources["memory_percent"]
        logger.debug("Memory usage: %.1f%%", memory_percent)

        if memory_percent >= self.config.memory_critical_threshold:
            logger.debug(
                "Memory CRITICAL: %.1f%% >= %.1f%%",
                memory_percent,
                self.config.memory_critical_threshold,
            )
            self.send_alert(
                alert_type=AlertType.RESOURCE,
                severity=AlertSeverity.CRITICAL,
                message=f"Critical memory usage: {memory_percent:.1f}%",
                metadata={"resources": resources},
            )
        elif memory_percent >= self.config.memory_warning_threshold:
            logger.debug(
                "Memory WARNING: %.1f%% >= %.1f%%",
                memory_percent,
                self.config.memory_warning_threshold,
            )
            self.send_alert(
                alert_type=AlertType.RESOURCE,
                severity=AlertSeverity.WARNING,
                message=f"High memory usage: {memory_percent:.1f}%",
                metadata={"resources": resources},
            )

        # Error rate check
        error_rate = metrics.get("recent", {}).get("errors", {}).get("error_rate", 0.0)
        logger.debug("Error rate: %.1f%%", error_rate * 100)

        if error_rate >= self.config.error_rate_threshold:
            logger.debug(
                "Error rate CRITICAL: %.1f%% >= %.1f%%",
                error_rate * 100,
                self.config.error_rate_threshold * 100,
            )
            self.send_alert(
                alert_type=AlertType.ERROR,
                severity=AlertSeverity.CRITICAL,
                message=f"High error rate: {error_rate:.1%}",
                metadata={"errors": health_check_result.get("errors", [])},
            )
        elif error_rate >= self.config.warning_rate_threshold:
            logger.debug(
                "Error rate WARNING: %.1f%% >= %.1f%%",
                error_rate * 100,
                self.config.warning_rate_threshold * 100,
            )
            self.send_alert(
                alert_type=AlertType.ERROR,
                severity=AlertSeverity.WARNING,
                message=f"Elevated error rate: {error_rate:.1%}",
                metadata={"errors": health_check_result.get("errors", [])},
            )

        logger.debug("Health check processing completed")
