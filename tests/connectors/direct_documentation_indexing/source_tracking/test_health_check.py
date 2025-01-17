"""Tests for health check functionality."""

from unittest.mock import patch

import pytest

from src.connectors.direct_documentation_indexing.source_tracking import (
    add_processing_step,
    calculate_health_status,
    log_error_or_warning,
)
from src.connectors.direct_documentation_indexing.source_tracking.document_operations import (
    add_document,
)
from src.connectors.direct_documentation_indexing.source_tracking.storage import LineageStorage
from src.core.monitoring.errors.models.log_entry import LogLevel
from src.core.monitoring.health.models import HealthStatus
from src.core.processing.steps.models.step import ProcessingStatus


@pytest.fixture
def temp_lineage_dir(tmp_path):
    """Create a temporary directory for test lineage data."""
    return tmp_path / "lineage"


@pytest.fixture
def storage(temp_lineage_dir):
    """Create a LineageStorage instance."""
    return LineageStorage(str(temp_lineage_dir))


def test_health_check_healthy(storage):
    """Test health check with healthy system state."""
    doc_id = "test_doc"
    add_document(storage, doc_id=doc_id)
    add_processing_step(
        storage, doc_id=doc_id, step_name="process", status=ProcessingStatus.SUCCESS
    )
    with patch("psutil.Process") as mock_process:
        mock_process.return_value.memory_info.return_value.rss = 100 * 1024 * 1024
        mock_process.return_value.memory_percent.return_value = 20.0
        mock_process.return_value.cpu_percent.return_value = 30.0
        health_status = calculate_health_status(storage)
        assert health_status.status == HealthStatus.HEALTHY
        assert not health_status.issues


def test_health_check_warning(storage):
    """Test health check with warning state."""
    doc_id = "test_doc"
    add_document(storage, doc_id=doc_id)
    log_error_or_warning(storage, doc_id=doc_id, level=LogLevel.WARNING, message="Test warning")
    with patch("psutil.Process") as mock_process:
        mock_process.return_value.memory_info.return_value.rss = 800 * 1024 * 1024
        mock_process.return_value.memory_percent.return_value = 80.0
        mock_process.return_value.cpu_percent.return_value = 85.0
        health_status = calculate_health_status(storage)
        assert health_status.status == HealthStatus.WARNING
        assert any("High" in issue for issue in health_status.issues)


def test_health_check_critical(storage):
    """Test health check with critical state."""
    doc_id = "test_doc"
    add_document(storage, doc_id=doc_id)
    log_error_or_warning(storage, doc_id=doc_id, level=LogLevel.ERROR, message="Test error")
    add_processing_step(storage, doc_id=doc_id, step_name="process", status=ProcessingStatus.FAILED)
    with patch("psutil.Process") as mock_process:
        mock_process.return_value.memory_info.return_value.rss = 950 * 1024 * 1024
        mock_process.return_value.memory_percent.return_value = 95.0
        mock_process.return_value.cpu_percent.return_value = 95.0
        health_status = calculate_health_status(storage)
        assert health_status.status == HealthStatus.CRITICAL
        assert any("Critical" in issue for issue in health_status.issues)


def test_health_check_with_thresholds(storage):
    """Test health check with custom thresholds."""
    custom_thresholds = {
        "memory_warning": 70.0,
        "memory_critical": 90.0,
        "cpu_warning": 75.0,
        "cpu_critical": 95.0,
    }
    with patch("psutil.Process") as mock_process:
        mock_process.return_value.memory_info.return_value.rss = 700 * 1024 * 1024
        mock_process.return_value.memory_percent.return_value = 70.0
        mock_process.return_value.cpu_percent.return_value = 75.0
        health_status = calculate_health_status(storage, thresholds=custom_thresholds)
        assert health_status.status == HealthStatus.WARNING
        assert any("memory" in issue.lower() for issue in health_status.issues)
        assert any("cpu" in issue.lower() for issue in health_status.issues)


def test_health_check_persistence(temp_lineage_dir):
    """Test persistence of health check data."""
    storage1 = LineageStorage(str(temp_lineage_dir))
    doc_id = "test_doc"
    add_document(storage1, doc_id=doc_id)
    log_error_or_warning(storage1, doc_id=doc_id, level=LogLevel.ERROR, message="Test error")
    storage2 = LineageStorage(str(temp_lineage_dir))
    health_status = calculate_health_status(storage2)
    assert health_status.status == HealthStatus.WARNING
    assert any("error" in issue.lower() for issue in health_status.issues)
