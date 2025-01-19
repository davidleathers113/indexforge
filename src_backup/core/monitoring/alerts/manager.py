"""
Core alert management implementation.

This module provides the main AlertManager class that handles alert creation,
distribution, and tracking across the system.
"""

from datetime import UTC, datetime, timedelta
from email.mime.text import MIMEText
import json
import logging
from pathlib import Path
import smtplib
from typing import Any

import requests

from src.core.monitoring.alerts.models import Alert, AlertConfig, AlertSeverity, AlertType


logger = logging.getLogger(__name__)


class AlertManager:
    """Manages system alerts and notifications.

    This class handles the creation, tracking, and distribution of system
    alerts through various notification channels. It supports email and
    webhook notifications with configurable thresholds and cooldown periods
    to prevent alert fatigue.

    Attributes:
        config: Alert configuration settings
        recent_alerts: Recently sent alerts
        alert_history: Historical record of alerts
    """

    def __init__(
        self,
        config_path: str | None = None,
        alert_config: AlertConfig | None = None,
    ) -> None:
        """Initialize the alert manager.

        Args:
            config_path: Path to JSON configuration file
            alert_config: Direct AlertConfig instance

        Raises:
            ValueError: If neither config_path nor alert_config is provided
            FileNotFoundError: If config_path is invalid
            json.JSONDecodeError: If config file is malformed
        """
        if not config_path and not alert_config:
            raise ValueError("Must provide either config_path or alert_config")

        self.config = alert_config or self._load_config(config_path)
        self.recent_alerts: dict[str, datetime] = {}
        self.alert_history: list[Alert] = []

    def _load_config(self, config_path: str | None) -> AlertConfig:
        """Load configuration from JSON file.

        Args:
            config_path: Path to configuration file

        Returns:
            Loaded AlertConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is malformed
            ValueError: If config values are invalid
        """
        if not config_path:
            return AlertConfig()

        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with config_file.open() as f:
                config_data = json.load(f)
            return AlertConfig(**config_data)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse config file: %s", e)
            raise
        except (TypeError, ValueError) as e:
            logger.error("Invalid config values: %s", e)
            raise ValueError(f"Invalid configuration: {e}")

    def send_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Send a new alert through configured channels.

        Args:
            alert_type: Type of alert
            severity: Alert severity level
            message: Alert message
            metadata: Additional context data

        Returns:
            True if alert was sent successfully

        Example:
            ```python
            manager.send_alert(
                alert_type=AlertType.ERROR,
                severity=AlertSeverity.CRITICAL,
                message="Database connection failed",
                metadata={"error": "Connection timeout"}
            )
            ```
        """
        alert = Alert(
            alert_type=alert_type,
            severity=severity,
            message=message,
            metadata=metadata or {},
        )

        if not self._should_send_alert(alert):
            logger.debug("Skipping alert due to cooldown: %s", alert.alert_id)
            return False

        success = True
        if self.config.email_config:
            success &= self._send_email_alert(alert)

        if self.config.webhook_urls:
            success &= self._send_webhook_alerts(alert)

        if success:
            self.recent_alerts[alert.alert_id] = alert.timestamp
            self.alert_history.append(alert)
            logger.info("Alert sent successfully: %s", alert.alert_id)

        return success

    def _should_send_alert(self, alert: Alert) -> bool:
        """Check if an alert should be sent based on cooldown period.

        Args:
            alert: Alert to check

        Returns:
            True if alert should be sent
        """
        # Always send critical alerts
        if alert.severity == AlertSeverity.CRITICAL:
            return True

        # Check for similar recent alerts
        cooldown = timedelta(seconds=self.config.alert_cooldown)
        now = datetime.now(UTC)

        for alert_id, timestamp in self.recent_alerts.items():
            if (
                alert_id.startswith(f"{alert.alert_type.value}_{alert.severity.value}")
                and now - timestamp < cooldown
            ):
                return False

        return True

    def _send_email_alert(self, alert: Alert) -> bool:
        """Send alert via email.

        Args:
            alert: Alert to send

        Returns:
            True if email was sent successfully
        """
        if not self.config.email_config:
            return False

        try:
            msg = MIMEText(
                f"Alert: {alert.message}\n"
                f"Type: {alert.alert_type.value}\n"
                f"Severity: {alert.severity.value}\n"
                f"Time: {alert.timestamp}\n"
                f"Metadata: {json.dumps(alert.metadata, indent=2)}"
            )

            msg["Subject"] = f"[{alert.severity.value.upper()}] {alert.message[:50]}"
            msg["From"] = self.config.email_config["from_address"]
            msg["To"] = self.config.email_config["to_address"]

            with smtplib.SMTP(
                self.config.email_config["smtp_host"],
                int(self.config.email_config["smtp_port"]),
            ) as server:
                if self.config.email_config.get("use_tls"):
                    server.starttls()
                if "username" in self.config.email_config:
                    server.login(
                        self.config.email_config["username"],
                        self.config.email_config["password"],
                    )
                server.send_message(msg)

            logger.info("Email alert sent: %s", alert.alert_id)
            return True

        except Exception as e:
            logger.error("Failed to send email alert: %s", e)
            return False

    def _send_webhook_alerts(self, alert: Alert) -> bool:
        """Send alert to configured webhooks.

        Args:
            alert: Alert to send

        Returns:
            True if all webhooks received alert successfully
        """
        if not self.config.webhook_urls:
            return False

        success = True
        payload = {
            "alert_id": alert.alert_id,
            "type": alert.alert_type.value,
            "severity": alert.severity.value,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
            "metadata": alert.metadata,
        }

        for name, url in self.config.webhook_urls.items():
            try:
                response = requests.post(url, json=payload, timeout=5.0)
                response.raise_for_status()
                logger.info("Webhook alert sent to %s: %s", name, alert.alert_id)
            except requests.exceptions.RequestException as e:
                logger.error("Failed to send webhook alert to %s: %s", name, e)
                success = False

        return success

    def check_and_alert(self, health_check_result: dict[str, Any]) -> None:
        """Check system health data and send alerts if needed.

        Args:
            health_check_result: System health metrics

        Example:
            ```python
            health_data = {
                "memory_usage": 85.5,
                "cpu_usage": 75.2,
                "error_rate": 0.02
            }
            manager.check_and_alert(health_data)
            ```
        """
        # Check memory usage
        if memory_usage := health_check_result.get("memory_usage"):
            if memory_usage >= self.config.memory_critical_threshold:
                self.send_alert(
                    AlertType.RESOURCE,
                    AlertSeverity.CRITICAL,
                    f"Critical memory usage: {memory_usage}%",
                    {"memory_usage": memory_usage},
                )
            elif memory_usage >= self.config.memory_warning_threshold:
                self.send_alert(
                    AlertType.RESOURCE,
                    AlertSeverity.WARNING,
                    f"High memory usage: {memory_usage}%",
                    {"memory_usage": memory_usage},
                )

        # Check CPU usage
        if cpu_usage := health_check_result.get("cpu_usage"):
            if cpu_usage >= self.config.cpu_critical_threshold:
                self.send_alert(
                    AlertType.RESOURCE,
                    AlertSeverity.CRITICAL,
                    f"Critical CPU usage: {cpu_usage}%",
                    {"cpu_usage": cpu_usage},
                )
            elif cpu_usage >= self.config.cpu_warning_threshold:
                self.send_alert(
                    AlertType.RESOURCE,
                    AlertSeverity.WARNING,
                    f"High CPU usage: {cpu_usage}%",
                    {"cpu_usage": cpu_usage},
                )

        # Check error rate
        if error_rate := health_check_result.get("error_rate"):
            if error_rate >= self.config.error_rate_threshold:
                self.send_alert(
                    AlertType.ERROR,
                    AlertSeverity.CRITICAL,
                    f"High error rate: {error_rate:.2%}",
                    {"error_rate": error_rate},
                )
            elif error_rate >= self.config.warning_rate_threshold:
                self.send_alert(
                    AlertType.ERROR,
                    AlertSeverity.WARNING,
                    f"Elevated error rate: {error_rate:.2%}",
                    {"error_rate": error_rate},
                )
