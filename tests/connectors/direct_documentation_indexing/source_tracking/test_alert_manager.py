"""Tests for alert management functionality."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
import pytest
from src.connectors.direct_documentation_indexing.source_tracking.alert_manager import Alert, AlertConfig, AlertManager, AlertSeverity, AlertType

@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary alert configuration file."""
    config = {'error_rate_threshold': 0.2, 'warning_rate_threshold': 0.1, 'memory_critical_threshold': 95.0, 'memory_warning_threshold': 85.0, 'email_config': {'smtp_host': 'smtp.test.com', 'smtp_port': '587', 'from_address': 'test@example.com', 'to_address': 'admin@example.com'}, 'webhook_urls': {'slack': 'https://hooks.slack.com/test', 'custom': 'https://api.custom.com/webhook'}}
    config_file = tmp_path / 'alert_config.json'
    with open(config_file, 'w') as f:
        json.dump(config, f)
    return str(config_file)

@pytest.fixture
def alert_manager(temp_config_file):
    """Create an AlertManager instance with test configuration."""
    return AlertManager(config_path=temp_config_file)

@pytest.fixture
def mock_send(mocker):
    """Mock the send function for alerts."""
    return mocker.patch('src.connectors.direct_documentation_indexing.source_tracking.alert_manager.AlertManager.send_alert')

def test_load_config(temp_config_file):
    """Test loading configuration from file."""
    manager = AlertManager(config_path=temp_config_file)
    assert manager.config.error_rate_threshold == 0.2
    assert manager.config.warning_rate_threshold == 0.1
    assert manager.config.memory_critical_threshold == 95.0
    assert manager.config.memory_warning_threshold == 85.0
    assert manager.config.email_config is not None
    assert len(manager.config.webhook_urls) == 2

def test_load_config_defaults():
    """Test loading default configuration."""
    manager = AlertManager()
    assert manager.config.error_rate_threshold == 0.1
    assert manager.config.warning_rate_threshold == 0.05
    assert manager.config.email_config is None
    assert not manager.config.webhook_urls

def test_send_alert_critical(alert_manager):
    """Test sending a critical alert."""
    with patch.object(alert_manager, '_send_email_alert') as mock_email:
        with patch.object(alert_manager, '_send_webhook_alerts') as mock_webhook:
            mock_email.return_value = True
            mock_webhook.return_value = True
            success = alert_manager.send_alert(alert_type=AlertType.ERROR, severity=AlertSeverity.CRITICAL, message='Test critical alert', metadata={'test_key': 'test_value'})
            assert success
            assert len(alert_manager.alert_history) == 1
            assert len(alert_manager.recent_alerts) == 1
            mock_email.assert_called_once()
            mock_webhook.assert_called_once()

def test_send_alert_warning(alert_manager):
    """Test sending a warning alert."""
    with patch.object(alert_manager, '_send_email_alert') as mock_email:
        with patch.object(alert_manager, '_send_webhook_alerts') as mock_webhook:
            mock_email.return_value = True
            mock_webhook.return_value = True
            success = alert_manager.send_alert(alert_type=AlertType.RESOURCE, severity=AlertSeverity.WARNING, message='Test warning alert')
            assert success
            assert len(alert_manager.alert_history) == 1
            assert len(alert_manager.recent_alerts) == 1
            mock_email.assert_not_called()
            mock_webhook.assert_called_once()

def test_alert_cooldown(alert_manager):
    """Test alert cooldown period."""
    with patch.object(alert_manager, '_send_webhook_alerts') as mock_webhook:
        mock_webhook.return_value = True
        success1 = alert_manager.send_alert(alert_type=AlertType.ERROR, severity=AlertSeverity.WARNING, message='First alert')
        success2 = alert_manager.send_alert(alert_type=AlertType.ERROR, severity=AlertSeverity.WARNING, message='Second alert')
        assert success1
        assert not success2
        assert len(alert_manager.alert_history) == 1
        assert mock_webhook.call_count == 1

def test_send_email_alert(alert_manager):
    """Test sending email alerts."""
    alert = Alert(alert_type=AlertType.ERROR, severity=AlertSeverity.CRITICAL, message='Test email alert')
    with patch('smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        success = alert_manager._send_email_alert(alert)
        assert success
        mock_smtp.assert_called_once_with(alert_manager.config.email_config['smtp_host'], int(alert_manager.config.email_config['smtp_port']))
        mock_server.send_message.assert_called_once()

def test_send_webhook_alerts(alert_manager):
    """Test sending webhook alerts."""
    alert = Alert(alert_type=AlertType.RESOURCE, severity=AlertSeverity.WARNING, message='Test webhook alert')
    with patch('requests.post') as mock_post:
        mock_post.return_value.raise_for_status = MagicMock()
        success = alert_manager._send_webhook_alerts(alert)
        assert success
        assert mock_post.call_count == 2
        for call in mock_post.call_args_list:
            args, kwargs = call
            assert kwargs['timeout'] == 5
            assert 'type' in kwargs['json']
            assert 'severity' in kwargs['json']
            assert 'message' in kwargs['json']

def test_check_and_alert(mock_send):
    """Test alert checking and sending."""
    manager = AlertManager()
    manager.check_and_alert({'status': 'critical', 'issues': ['Critical memory usage', 'High error rate'], 'metrics': {'recent': {'errors': {'error_rate': 0.15}}}, 'resources': {'memory_percent': 92.0, 'cpu_percent': 85.0}, 'errors': ['Test error']})
    mock_send.assert_any_call(alert_type=AlertType.HEALTH, severity=AlertSeverity.CRITICAL, message='System health critical: Critical memory usage, High error rate', metadata={'metrics': {'recent': {'errors': {'error_rate': 0.15}}}, 'resources': {'memory_percent': 92.0, 'cpu_percent': 85.0}})
    mock_send.assert_any_call(alert_type=AlertType.RESOURCE, severity=AlertSeverity.CRITICAL, message='Critical memory usage: 92.0%', metadata={'resources': {'memory_percent': 92.0, 'cpu_percent': 85.0}})
    mock_send.assert_any_call(alert_type=AlertType.ERROR, severity=AlertSeverity.CRITICAL, message='High error rate: 15.0%', metadata={'errors': ['Test error']})