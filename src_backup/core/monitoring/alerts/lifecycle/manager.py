"""Alert lifecycle management implementation.

This module provides the AlertLifecycleManager class for handling the complete
lifecycle of alerts, including creation, notification, and state management.
"""

from datetime import UTC, datetime
from email.mime.text import MIMEText
import logging
import smtplib
from typing import Any

import requests

from ..models.alert import Alert
from ..models.config import AlertConfig
from ..models.types import AlertSeverity, AlertType


logger = logging.getLogger(__name__)


class AlertLifecycleManager:
    """Manages the lifecycle of system alerts.

    This class handles alert creation, notification delivery, and state tracking.
    It ensures proper validation and delivery of alerts through configured
    notification channels while managing alert cooldown periods and retries.

    Example:
        ```python
        config = AlertConfig(
            memory_critical_threshold=90.0,
            email_config={
                "smtp_host": "smtp.example.com",
                "smtp_port": "587",
                "from_address": "alerts@example.com",
                "to_address": "admin@example.com",
            }
        )

        manager = AlertLifecycleManager(config)
        alert = manager.create_alert(
            AlertType.RESOURCE,
            AlertSeverity.WARNING,
            "High memory usage detected",
            {"memory_usage": 85.5}
        )
        ```

    Attributes:
        config: Alert configuration settings
        recent_alerts: Cache of recently sent alerts
        alert_history: Historical record of all alerts
    """

    def __init__(self, config: AlertConfig) -> None:
        """Initialize the alert lifecycle manager.

        Args:
            config: Alert configuration instance
        """
        self.config = config
        self.recent_alerts: dict[str, datetime] = {}
        self.alert_history: list[Alert] = []

    def create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> Alert:
        """Create and process a new alert.

        Args:
            alert_type: Type of alert to create
            severity: Alert severity level
            message: Alert message
            metadata: Additional alert context

        Returns:
            Created and processed alert instance

        Example:
            ```python
            alert = manager.create_alert(
                AlertType.RESOURCE,
                AlertSeverity.WARNING,
                "High memory usage detected",
                {"memory_usage": 85.5}
            )
            ```
        """
        alert = Alert(
            alert_type=alert_type,
            severity=severity,
            message=message,
            metadata=metadata or {},
        )
        self.process_alert(alert)
        return alert

    def process_alert(self, alert: Alert) -> bool:
        """Process an alert through configured notification channels.

        Args:
            alert: Alert to process

        Returns:
            True if alert was processed successfully

        Example:
            ```python
            success = manager.process_alert(alert)
            if not success:
                logger.error("Failed to process alert: %s", alert.alert_id)
            ```
        """
        if not self._should_process_alert(alert):
            logger.debug("Skipping alert due to cooldown: %s", alert.alert_id)
            return False

        success = True
        if self.config.email_config:
            success &= self._send_email_notification(alert)

        if self.config.webhook_urls:
            success &= self._send_webhook_notifications(alert)

        if success:
            self.recent_alerts[alert.alert_id] = alert.timestamp
            self.alert_history.append(alert)
            logger.info("Alert processed successfully: %s", alert.alert_id)

        return success

    def _should_process_alert(self, alert: Alert) -> bool:
        """Check if an alert should be processed based on cooldown period.

        Args:
            alert: Alert to check

        Returns:
            True if alert should be processed
        """
        if alert.requires_immediate_action:
            return True

        now = datetime.now(UTC)
        for alert_id, timestamp in self.recent_alerts.items():
            if (
                alert_id.startswith(f"{alert.alert_type.value}_{alert.severity.value}")
                and (now - timestamp).total_seconds() < self.config.alert_cooldown
            ):
                return False

        return True

    def _send_email_notification(self, alert: Alert) -> bool:
        """Send alert via email notification.

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
                f"Metadata: {alert.metadata}"
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

            logger.info("Email notification sent: %s", alert.alert_id)
            return True

        except Exception as e:
            logger.error("Failed to send email notification: %s", e)
            return False

    def _send_webhook_notifications(self, alert: Alert) -> bool:
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
            retries = self.config.max_retries
            while retries > 0:
                try:
                    response = requests.post(url, json=payload, timeout=5.0)
                    response.raise_for_status()
                    logger.info("Webhook notification sent to %s: %s", name, alert.alert_id)
                    break
                except requests.exceptions.RequestException as e:
                    retries -= 1
                    if retries == 0:
                        logger.error("Failed to send webhook notification to %s: %s", name, e)
                        success = False
                    else:
                        logger.warning(
                            "Webhook notification retry (%d remaining) for %s: %s",
                            retries,
                            name,
                            e,
                        )

        return success
