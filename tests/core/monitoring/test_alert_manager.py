"""Tests for the core alert management system."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.core.monitoring.alerts.lifecycle.manager import AlertLifecycleManager
from src.core.monitoring.alerts.models.alert import Alert
from src.core.monitoring.alerts.models.config import AlertConfig
from src.core.monitoring.alerts.models.types import AlertSeverity, AlertType


@pytest.fixture
def alert_config() -> AlertConfig:
    """Create a test alert configuration."""
    return AlertConfig(
        error_rate_threshold=0.1,
        warning_rate_threshold=0.05,
        memory_critical_threshold=90.0,
        memory_warning_threshold=80.0,
        cpu_critical_threshold=90.0,
        cpu_warning_threshold=80.0,
        alert_cooldown=300,
        email_config={
            "smtp_host": "test.smtp.com",
            "smtp_port": "587",
            "from_address": "test@example.com",
            "to_address": "admin@example.com",
        },
        webhook_urls={"test": "http://test.webhook.com/alert"},
    )


@pytest.fixture
def alert_manager(alert_config: AlertConfig) -> AlertLifecycleManager:
    """Create a test alert manager instance."""
    return AlertLifecycleManager(alert_config=alert_config)


def test_alert_manager_initialization(alert_config: AlertConfig) -> None:
    """Test alert manager initialization with config."""
    manager = AlertLifecycleManager(alert_config=alert_config)
    assert manager.config == alert_config
    assert not manager.recent_alerts
    assert not manager.alert_history


def test_alert_manager_initialization_without_config() -> None:
    """Test alert manager initialization fails without config."""
    with pytest.raises(ValueError):
        AlertLifecycleManager()


def test_load_config_from_file(tmp_path: Path) -> None:
    """Test loading configuration from JSON file."""
    config_data = {
        "error_rate_threshold": 0.1,
        "warning_rate_threshold": 0.05,
        "memory_critical_threshold": 90.0,
        "memory_warning_threshold": 80.0,
        "alert_cooldown": 300,
    }
    config_file = tmp_path / "test_config.json"
    config_file.write_text(json.dumps(config_data))

    manager = AlertLifecycleManager(config_path=str(config_file))
    assert manager.config.error_rate_threshold == 0.1
    assert manager.config.memory_critical_threshold == 90.0


def test_load_config_invalid_file() -> None:
    """Test loading configuration from non-existent file fails."""
    with pytest.raises(FileNotFoundError):
        AlertLifecycleManager(config_path="/nonexistent/config.json")


def test_send_alert(alert_manager: AlertLifecycleManager) -> None:
    """Test sending an alert."""
    with patch("smtplib.SMTP") as mock_smtp, patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200

        success = alert_manager.send_alert(
            AlertType.ERROR,
            AlertSeverity.CRITICAL,
            "Test alert",
            {"test": "data"},
        )

        assert success
        assert len(alert_manager.alert_history) == 1
        assert len(alert_manager.recent_alerts) == 1
        mock_smtp.assert_called_once()
        mock_post.assert_called_once()


def test_alert_cooldown(alert_manager: AlertLifecycleManager) -> None:
    """Test alert cooldown period."""
    # Send first alert
    with patch("smtplib.SMTP"), patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        alert_manager.send_alert(
            AlertType.ERROR,
            AlertSeverity.WARNING,
            "Test alert",
        )

    # Try to send similar alert within cooldown period
    with patch("smtplib.SMTP"), patch("requests.post") as mock_post:
        success = alert_manager.send_alert(
            AlertType.ERROR,
            AlertSeverity.WARNING,
            "Another test alert",
        )
        assert not success
        mock_post.assert_not_called()


def test_critical_alerts_bypass_cooldown(alert_manager: AlertLifecycleManager) -> None:
    """Test that critical alerts bypass the cooldown period."""
    # Send first critical alert
    with patch("smtplib.SMTP"), patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        alert_manager.send_alert(
            AlertType.ERROR,
            AlertSeverity.CRITICAL,
            "Critical alert 1",
        )

    # Send another critical alert immediately
    with patch("smtplib.SMTP"), patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        success = alert_manager.send_alert(
            AlertType.ERROR,
            AlertSeverity.CRITICAL,
            "Critical alert 2",
        )
        assert success
        mock_post.assert_called_once()


def test_email_alert_failure(alert_manager: AlertLifecycleManager) -> None:
    """Test handling of email sending failure."""
    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.side_effect = Exception("SMTP error")
        success = alert_manager.send_alert(
            AlertType.ERROR,
            AlertSeverity.CRITICAL,
            "Test alert",
        )
        assert not success
        assert not alert_manager.alert_history


def test_webhook_alert_failure(alert_manager: AlertLifecycleManager) -> None:
    """Test handling of webhook sending failure."""
    with patch("smtplib.SMTP"), patch("requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.RequestException("Webhook error")
        success = alert_manager.send_alert(
            AlertType.ERROR,
            AlertSeverity.CRITICAL,
            "Test alert",
        )
        assert not success
        assert not alert_manager.alert_history


def test_check_and_alert_memory(alert_manager: AlertLifecycleManager) -> None:
    """Test health check alerts for memory usage."""
    with patch.object(alert_manager, "send_alert") as mock_send:
        # Test critical memory
        alert_manager.check_and_alert({"memory_usage": 95.0})
        mock_send.assert_called_with(
            AlertType.RESOURCE,
            AlertSeverity.CRITICAL,
            "Critical memory usage: 95.0%",
            {"memory_usage": 95.0},
        )

        mock_send.reset_mock()

        # Test warning memory
        alert_manager.check_and_alert({"memory_usage": 85.0})
        mock_send.assert_called_with(
            AlertType.RESOURCE,
            AlertSeverity.WARNING,
            "High memory usage: 85.0%",
            {"memory_usage": 85.0},
        )


def test_check_and_alert_cpu(alert_manager: AlertLifecycleManager) -> None:
    """Test health check alerts for CPU usage."""
    with patch.object(alert_manager, "send_alert") as mock_send:
        # Test critical CPU
        alert_manager.check_and_alert({"cpu_usage": 95.0})
        mock_send.assert_called_with(
            AlertType.RESOURCE,
            AlertSeverity.CRITICAL,
            "Critical CPU usage: 95.0%",
            {"cpu_usage": 95.0},
        )

        mock_send.reset_mock()

        # Test warning CPU
        alert_manager.check_and_alert({"cpu_usage": 85.0})
        mock_send.assert_called_with(
            AlertType.RESOURCE,
            AlertSeverity.WARNING,
            "High CPU usage: 85.0%",
            {"cpu_usage": 85.0},
        )


def test_check_and_alert_error_rate(alert_manager: AlertLifecycleManager) -> None:
    """Test health check alerts for error rate."""
    with patch.object(alert_manager, "send_alert") as mock_send:
        # Test critical error rate
        alert_manager.check_and_alert({"error_rate": 0.15})
        mock_send.assert_called_with(
            AlertType.ERROR,
            AlertSeverity.CRITICAL,
            "High error rate: 15.00%",
            {"error_rate": 0.15},
        )

        mock_send.reset_mock()

        # Test warning error rate
        alert_manager.check_and_alert({"error_rate": 0.07})
        mock_send.assert_called_with(
            AlertType.ERROR,
            AlertSeverity.WARNING,
            "Elevated error rate: 7.00%",
            {"error_rate": 0.07},
        )
