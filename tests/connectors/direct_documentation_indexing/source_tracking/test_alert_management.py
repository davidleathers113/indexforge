"""Tests for alert history and management functionality."""

from datetime import datetime, timezone
from unittest.mock import patch


from src.connectors.direct_documentation_indexing.source_tracking.alert_manager import (
    Alert,
    AlertSeverity,
    AlertType,
)


def test_alert_id_generation():
    """Test alert ID generation and uniqueness."""
    alert1 = Alert(
        alert_type=AlertType.ERROR, severity=AlertSeverity.CRITICAL, message="Test alert 1"
    )
    alert2 = Alert(
        alert_type=AlertType.ERROR, severity=AlertSeverity.CRITICAL, message="Test alert 2"
    )

    assert alert1.alert_id != alert2.alert_id, "Alert IDs should be unique"
    assert alert1.alert_type.value in alert1.alert_id, "Alert ID should contain alert type"
    assert alert1.severity.value in alert1.alert_id, "Alert ID should contain severity"


def test_alert_history(alert_manager):
    """Test alert history tracking."""
    metadata = {"test_key": "test_value", "timestamp": datetime.now(timezone.utc)}

    with patch.object(alert_manager, "_send_webhook_alerts", return_value=True):
        alert_manager.send_alert(
            alert_type=AlertType.ERROR,
            severity=AlertSeverity.WARNING,
            message="Test alert",
            metadata=metadata,
        )

        alert = alert_manager.alert_history[0]
        assert alert.metadata == metadata, "Metadata should be preserved"
        assert isinstance(alert.timestamp, datetime), "Timestamp should be datetime"


def test_alert_cooldown(alert_manager):
    """Test alert cooldown period."""
    with patch.object(alert_manager, "_send_webhook_alerts", return_value=True):
        success1 = alert_manager.send_alert(
            alert_type=AlertType.ERROR, severity=AlertSeverity.WARNING, message="First alert"
        )
        success2 = alert_manager.send_alert(
            alert_type=AlertType.ERROR, severity=AlertSeverity.WARNING, message="Second alert"
        )

        assert success1, "First alert should be sent"
        assert not success2, "Second alert should be blocked by cooldown"
