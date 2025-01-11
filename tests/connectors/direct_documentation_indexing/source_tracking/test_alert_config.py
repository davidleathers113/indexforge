"""Tests for alert configuration loading and validation."""

import json

import pytest

from src.connectors.direct_documentation_indexing.source_tracking.alert_manager import AlertManager


@pytest.fixture
def temp_config_file(tmp_path, test_alert_config):
    """Create a temporary alert configuration file."""
    config_file = tmp_path / "alert_config.json"
    config_dict = {
        "error_rate_threshold": test_alert_config.error_rate_threshold,
        "warning_rate_threshold": test_alert_config.warning_rate_threshold,
        "memory_critical_threshold": test_alert_config.memory_critical_threshold,
        "memory_warning_threshold": test_alert_config.memory_warning_threshold,
        "email_config": test_alert_config.email_config,
        "webhook_urls": test_alert_config.webhook_urls,
    }
    with open(config_file, "w") as f:
        json.dump(config_dict, f)
    return str(config_file)


def test_load_config(temp_config_file):
    """Test loading configuration from file."""
    manager = AlertManager(config_path=temp_config_file)
    assert manager.config.error_rate_threshold == 0.2, "Error rate threshold mismatch"
    assert manager.config.warning_rate_threshold == 0.1, "Warning rate threshold mismatch"
    assert manager.config.memory_critical_threshold == 95.0, "Memory critical threshold mismatch"
    assert manager.config.memory_warning_threshold == 85.0, "Memory warning threshold mismatch"
    assert manager.config.email_config is not None, "Email config should be present"
    assert len(manager.config.webhook_urls) == 2, "Should have two webhook URLs"


def test_load_config_defaults():
    """Test loading default configuration."""
    manager = AlertManager()
    assert manager.config.error_rate_threshold == 0.1, "Default error rate threshold mismatch"
    assert manager.config.warning_rate_threshold == 0.05, "Default warning rate threshold mismatch"
    assert manager.config.email_config is None, "Default email config should be None"
    assert not manager.config.webhook_urls, "Default webhook URLs should be empty"


def test_invalid_config_path():
    """Test handling of invalid configuration file path."""
    with pytest.raises(FileNotFoundError):
        AlertManager(config_path="nonexistent.json")
