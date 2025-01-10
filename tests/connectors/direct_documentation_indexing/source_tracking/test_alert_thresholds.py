"""Tests for alert threshold monitoring and triggering."""

import pytest

from src.connectors.direct_documentation_indexing.source_tracking.alert_manager import (
    AlertSeverity,
    AlertType,
)


@pytest.fixture
def mock_send(mocker):
    """Mock the send function for alerts."""
    return mocker.patch(
        "src.connectors.direct_documentation_indexing.source_tracking.alert_manager.AlertManager.send_alert"
    )


def test_cpu_threshold_warning(alert_manager, mock_send):
    """Test CPU usage warning threshold."""
    alert_manager.check_and_alert(
        {
            "status": "warning",
            "resources": {"cpu_percent": 85.0},
        }
    )

    mock_send.assert_called_with(
        alert_type=AlertType.RESOURCE,
        severity=AlertSeverity.WARNING,
        message="High CPU usage: 85.0%",
        metadata={"resources": {"cpu_percent": 85.0}},
    )


def test_memory_threshold_critical(alert_manager, mock_send):
    """Test memory usage critical threshold."""
    alert_manager.check_and_alert(
        {
            "status": "critical",
            "resources": {"memory_percent": 96.0},
        }
    )

    mock_send.assert_called_with(
        alert_type=AlertType.RESOURCE,
        severity=AlertSeverity.CRITICAL,
        message="Critical memory usage: 96.0%",
        metadata={"resources": {"memory_percent": 96.0}},
    )


def test_disk_threshold_warning(alert_manager, mock_send):
    """Test disk usage warning threshold."""
    alert_manager.check_and_alert(
        {
            "status": "warning",
            "resources": {"disk_percent": 82.0},
        }
    )

    mock_send.assert_called_with(
        alert_type=AlertType.RESOURCE,
        severity=AlertSeverity.WARNING,
        message="High disk usage: 82.0%",
        metadata={"resources": {"disk_percent": 82.0}},
    )


def test_invalid_threshold_data(alert_manager, mock_send):
    """Test handling of invalid threshold data."""
    alert_manager.check_and_alert(
        {
            "status": "warning",
            "resources": {"cpu_percent": "invalid"},
        }
    )
    mock_send.assert_not_called()


def test_missing_resource_data(alert_manager, mock_send):
    """Test handling of missing resource data."""
    alert_manager.check_and_alert({"status": "warning"})
    mock_send.assert_not_called()


def test_below_threshold_values(alert_manager, mock_send):
    """Test that alerts are not triggered for normal values."""
    alert_manager.check_and_alert(
        {
            "status": "normal",
            "resources": {
                "cpu_percent": 50.0,
                "memory_percent": 60.0,
                "disk_percent": 70.0,
            },
        }
    )
    mock_send.assert_not_called()
