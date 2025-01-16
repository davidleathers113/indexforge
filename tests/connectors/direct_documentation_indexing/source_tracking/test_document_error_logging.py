"""Tests for document error logging functionality."""

from datetime import UTC, datetime, timedelta

import pytest

from src.connectors.direct_documentation_indexing.source_tracking import (
    add_document,
    log_error_or_warning,
)
from src.connectors.direct_documentation_indexing.source_tracking.enums import LogLevel
from src.connectors.direct_documentation_indexing.source_tracking.storage import LineageStorage


@pytest.fixture
def temp_lineage_dir(tmp_path):
    """Create a temporary directory for test lineage data."""
    return tmp_path / "lineage"


@pytest.fixture
def storage(temp_lineage_dir):
    """Create a LineageStorage instance."""
    return LineageStorage(str(temp_lineage_dir))


def test_log_error_or_warning(storage):
    """Test logging errors and warnings."""
    doc_id = "test_doc"
    add_document(storage, doc_id=doc_id)
    log_error_or_warning(storage, doc_id=doc_id, level=LogLevel.ERROR, message="Test error")
    logs = storage.get_lineage(doc_id).error_logs
    assert len(logs) == 1
    assert logs[0].log_level == LogLevel.ERROR
    assert logs[0].message == "Test error"


def test_log_error_or_warning_invalid_level(storage):
    """Test logging with invalid level."""
    doc_id = "test_doc"
    add_document(storage, doc_id=doc_id)
    with pytest.raises(ValueError):
        log_error_or_warning(storage, doc_id=doc_id, level="invalid_level", message="Test")


def test_log_error_or_warning_missing_doc(storage):
    """Test logging for non-existent document."""
    with pytest.raises(ValueError):
        log_error_or_warning(storage, doc_id="non_existent", level=LogLevel.ERROR, message="Test")


def test_get_error_logs_filtered(storage):
    """Test filtering error logs by level."""
    doc_id = "test_doc"
    add_document(storage, doc_id=doc_id)
    log_error_or_warning(storage, doc_id=doc_id, level=LogLevel.ERROR, message="Test error")
    log_error_or_warning(storage, doc_id=doc_id, level=LogLevel.WARNING, message="Test warning")
    error_logs = [
        log for log in storage.get_lineage(doc_id).error_logs if log.log_level == LogLevel.ERROR
    ]
    warning_logs = [
        log for log in storage.get_lineage(doc_id).error_logs if log.log_level == LogLevel.WARNING
    ]
    assert len(error_logs) == 1
    assert len(warning_logs) == 1
    assert error_logs[0].message == "Test error"
    assert warning_logs[0].message == "Test warning"


def test_get_error_logs_time_filtered(storage):
    """Test filtering error logs by time range."""
    doc_id = "test_doc"
    add_document(storage, doc_id=doc_id)
    now = datetime.now(UTC)
    old_time = now - timedelta(hours=2)
    recent_time = now - timedelta(minutes=30)
    log_error_or_warning(
        storage, doc_id=doc_id, level=LogLevel.ERROR, message="Old error", timestamp=old_time
    )
    log_error_or_warning(
        storage, doc_id=doc_id, level=LogLevel.ERROR, message="Recent error", timestamp=recent_time
    )
    recent_logs = [
        log
        for log in storage.get_lineage(doc_id).error_logs
        if log.timestamp >= now - timedelta(hours=1)
    ]
    assert len(recent_logs) == 1
    assert recent_logs[0].message == "Recent error"


def test_error_logs_persistence(temp_lineage_dir):
    """Test persistence of error logs."""
    storage1 = LineageStorage(str(temp_lineage_dir))
    doc_id = "test_doc"
    add_document(storage1, doc_id=doc_id)
    log_error_or_warning(storage1, doc_id=doc_id, level=LogLevel.ERROR, message="Test error")
    storage2 = LineageStorage(str(temp_lineage_dir))
    lineage = storage2.get_lineage(doc_id)
    assert lineage is not None, f"Document {doc_id} not found in storage2"
    logs = lineage.error_logs
    assert len(logs) == 1
    assert logs[0].log_level == LogLevel.ERROR
    assert logs[0].message == "Test error"
