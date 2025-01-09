"""Tests for error logging functionality."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from src.connectors.direct_documentation_indexing.source_tracking.enums import LogLevel
from src.connectors.direct_documentation_indexing.source_tracking.lineage_manager import DocumentLineageManager
from src.connectors.direct_documentation_indexing.source_tracking.models import DocumentLineage

@pytest.fixture
def temp_lineage_dir(tmp_path):
    """Create a temporary directory for test lineage data."""
    return tmp_path / 'lineage'

@pytest.fixture
def lineage_manager(temp_lineage_dir):
    """Create a DocumentLineageManager instance."""
    return DocumentLineageManager(str(temp_lineage_dir))

def test_log_error(lineage_manager):
    """Test logging an error."""
    doc_id = 'test_doc'
    lineage_manager.add_document(doc_id=doc_id)
    error_message = 'Test error message'
    lineage_manager.log_error_or_warning(doc_id=doc_id, log_level=LogLevel.ERROR, message=error_message)
    logs = lineage_manager.get_error_logs(doc_id)
    assert len(logs) == 1
    assert logs[0].log_level == LogLevel.ERROR
    assert logs[0].message == error_message
    assert logs[0].timestamp is not None

def test_log_warning(lineage_manager):
    """Test logging a warning."""
    doc_id = 'test_doc'
    lineage_manager.add_document(doc_id=doc_id)
    warning_message = 'Test warning message'
    lineage_manager.log_error_or_warning(doc_id=doc_id, log_level=LogLevel.WARNING, message=warning_message)
    logs = lineage_manager.get_error_logs(doc_id)
    assert len(logs) == 1
    assert logs[0].log_level == LogLevel.WARNING
    assert logs[0].message == warning_message
    assert logs[0].timestamp is not None

def test_log_multiple_errors(lineage_manager):
    """Test logging multiple errors for a document."""
    doc_id = 'test_doc'
    lineage_manager.add_document(doc_id=doc_id)
    error_messages = ['First error', 'Second error', 'Third error']
    for message in error_messages:
        lineage_manager.log_error_or_warning(doc_id=doc_id, log_level=LogLevel.ERROR, message=message)
    logs = lineage_manager.get_error_logs(doc_id)
    assert len(logs) == len(error_messages)
    for log, message in zip(logs, error_messages):
        assert log.log_level == LogLevel.ERROR
        assert log.message == message

def test_log_error_missing_doc(lineage_manager):
    """Test logging an error for a non-existent document."""
    with pytest.raises(ValueError, match='not found'):
        lineage_manager.log_error_or_warning(doc_id='non_existent', log_level=LogLevel.ERROR, message='Test error')

def test_get_error_logs_filtered(lineage_manager):
    """Test filtering error logs by level."""
    doc_id = 'test_doc'
    lineage_manager.add_document(doc_id=doc_id)
    lineage_manager.log_error_or_warning(doc_id=doc_id, log_level=LogLevel.ERROR, message='Test error')
    lineage_manager.log_error_or_warning(doc_id=doc_id, log_level=LogLevel.WARNING, message='Test warning')
    error_logs = lineage_manager.get_error_logs(doc_id=doc_id, log_level=LogLevel.ERROR)
    assert len(error_logs) == 1
    assert error_logs[0].log_level == LogLevel.ERROR
    warning_logs = lineage_manager.get_error_logs(doc_id=doc_id, log_level=LogLevel.WARNING)
    assert len(warning_logs) == 1
    assert warning_logs[0].log_level == LogLevel.WARNING

def test_get_error_logs_time_filtered(lineage_manager):
    """Test filtering error logs by time range."""
    doc_id = 'test_doc'
    lineage_manager.add_document(doc_id=doc_id)
    lineage_manager.log_error_or_warning(doc_id=doc_id, log_level=LogLevel.ERROR, message='Test error')
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)
    recent_logs = lineage_manager.get_error_logs(doc_id=doc_id, start_time=one_hour_ago)
    assert len(recent_logs) == 1
    old_logs = lineage_manager.get_error_logs(doc_id=doc_id, end_time=now - timedelta(hours=2))
    assert len(old_logs) == 0

def test_error_log_persistence(temp_lineage_dir):
    """Test persistence of error logs."""
    manager1 = DocumentLineageManager(str(temp_lineage_dir))
    doc_id = 'test_doc'
    manager1.add_document(doc_id=doc_id)
    manager1.log_error_or_warning(doc_id=doc_id, log_level=LogLevel.ERROR, message='Test error')
    manager2 = DocumentLineageManager(str(temp_lineage_dir))
    logs = manager2.get_error_logs(doc_id)
    assert len(logs) == 1
    assert logs[0].log_level == LogLevel.ERROR
    assert logs[0].message == 'Test error'