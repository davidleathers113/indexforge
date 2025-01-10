"""Tests for alert notification delivery mechanisms."""

import smtplib
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from src.connectors.direct_documentation_indexing.source_tracking.alert_manager import (
    Alert,
    AlertSeverity,
    AlertType,
)


@pytest.fixture
def test_alert():
    """Create a test alert."""
    return Alert(alert_type=AlertType.ERROR, severity=AlertSeverity.CRITICAL, message="Test alert")


def test_send_email_alert(alert_manager, test_alert):
    """Test sending email alerts."""
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        success = alert_manager._send_email_alert(test_alert)

        assert success, "Email alert should be sent successfully"
        mock_smtp.assert_called_once_with(
            alert_manager.config.email_config["smtp_host"],
            int(alert_manager.config.email_config["smtp_port"]),
        )
        mock_server.send_message.assert_called_once()


def test_email_connection_failure(alert_manager, test_alert):
    """Test handling of SMTP connection failures."""
    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.side_effect = smtplib.SMTPConnectError(code=421, msg="Connection refused")
        success = alert_manager._send_email_alert(test_alert)
        assert not success, "Should handle SMTP connection failure gracefully"


def test_send_webhook_alerts(alert_manager, test_alert):
    """Test sending webhook alerts."""
    with patch("requests.post") as mock_post:
        mock_post.return_value.raise_for_status = Mock()
        success = alert_manager._send_webhook_alerts(test_alert)

        assert success, "Webhook alerts should be sent successfully"
        assert mock_post.call_count == 2, "Should call both webhook endpoints"


def test_webhook_partial_failure(alert_manager, test_alert):
    """Test webhook delivery with partial failures."""

    def mock_post_with_failure(*args, **kwargs):
        """Mock POST request with conditional failure."""
        if "slack" in args[0]:
            response = Mock()
            response.raise_for_status.side_effect = requests.RequestException
            return response
        response = Mock()
        response.raise_for_status.return_value = None
        return response

    with patch("requests.post", side_effect=mock_post_with_failure):
        success = alert_manager._send_webhook_alerts(test_alert)
        assert success, "Should succeed if at least one webhook succeeds"


def test_webhook_complete_failure(alert_manager, test_alert):
    """Test handling of complete webhook delivery failure."""
    with patch("requests.post") as mock_post:
        mock_post.side_effect = requests.RequestException("Connection error")
        success = alert_manager._send_webhook_alerts(test_alert)
        assert not success, "Should handle complete webhook failure gracefully"


def test_alert_with_invalid_metadata(alert_manager):
    """Test alert creation with invalid metadata."""
    with pytest.raises(TypeError):
        Alert(
            alert_type=AlertType.ERROR,
            severity=AlertSeverity.WARNING,
            message="Test alert",
            metadata={"invalid": object()},  # Non-serializable object
        )
