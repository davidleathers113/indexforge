"""Tests for deprecation warnings and import compatibility.

This module verifies that:
1. Deprecated imports emit appropriate warnings
2. Both old and new import paths work correctly
3. Imported classes maintain functionality
"""

import pytest

from src.core.monitoring.alerts.models.alert import Alert as NewAlert
from src.core.monitoring.alerts.models.config import AlertConfig as NewConfig
from src.core.monitoring.alerts.models.types import (
    AlertSeverity as NewSeverity,
    AlertType as NewType,
)


def test_deprecated_imports():
    """Verify that deprecated imports emit warnings but still work."""
    with pytest.warns(DeprecationWarning) as warnings:
        from src.core.monitoring.alerts.models import (
            Alert,
            AlertConfig,
            AlertSeverity,
            AlertType,
        )

    # Check warning message
    assert len(warnings) == 1
    assert "deprecated" in str(warnings[0].message)
    assert "2.0.0" in str(warnings[0].message)

    # Verify imported classes match new path classes
    assert Alert is NewAlert
    assert AlertConfig is NewConfig
    assert AlertType is NewType
    assert AlertSeverity is NewSeverity


def test_deprecated_import_functionality():
    """Verify that deprecated imports maintain full functionality."""
    with pytest.warns(DeprecationWarning):
        from src.core.monitoring.alerts.models import Alert, AlertSeverity, AlertType

    # Create alert using deprecated imports
    alert = Alert(
        alert_type=AlertType.ERROR,
        severity=AlertSeverity.CRITICAL,
        message="Test alert",
    )

    # Verify all functionality works
    assert alert.alert_type == AlertType.ERROR
    assert alert.severity == AlertSeverity.CRITICAL
    assert alert.message == "Test alert"
    assert not alert.acknowledged
    assert not alert.resolved

    # Test methods
    alert.acknowledge()
    assert alert.acknowledged

    alert.resolve(notes="Test resolution")
    assert alert.resolved
    assert alert.resolution_notes == "Test resolution"


def test_new_import_paths():
    """Verify that new import paths work without warnings."""
    with pytest.warns(None) as warnings:
        from src.core.monitoring.alerts.models.alert import Alert
        from src.core.monitoring.alerts.models.config import AlertConfig
        from src.core.monitoring.alerts.models.types import AlertSeverity, AlertType

        # Create objects to ensure imports work
        alert = Alert(
            alert_type=AlertType.ERROR,
            severity=AlertSeverity.CRITICAL,
            message="Test alert",
        )
        config = AlertConfig()

    # Verify no warnings were emitted
    assert len(warnings) == 0

    # Verify objects work correctly
    assert isinstance(alert, Alert)
    assert isinstance(config, AlertConfig)
    assert alert.alert_type == AlertType.ERROR
    assert alert.severity == AlertSeverity.CRITICAL
