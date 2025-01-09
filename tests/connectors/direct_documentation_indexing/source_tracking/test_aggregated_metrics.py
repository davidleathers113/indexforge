"""Tests for aggregated metrics functionality."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
import pytest
from src.connectors.direct_documentation_indexing.source_tracking import add_processing_step, get_aggregated_metrics, get_real_time_status, log_error_or_warning
from src.connectors.direct_documentation_indexing.source_tracking.document_operations import add_document
from src.connectors.direct_documentation_indexing.source_tracking.enums import LogLevel, ProcessingStatus
from src.connectors.direct_documentation_indexing.source_tracking.models import DocumentLineage
from src.connectors.direct_documentation_indexing.source_tracking.storage import LineageStorage

@pytest.fixture
def temp_lineage_dir(tmp_path):
    """Create a temporary directory for test lineage data."""
    return tmp_path / 'lineage'

@pytest.fixture
def storage(temp_lineage_dir):
    """Create a LineageStorage instance."""
    return LineageStorage(str(temp_lineage_dir))

def test_get_aggregated_metrics_empty(storage):
    """Test getting aggregated metrics with no documents."""
    metrics = get_aggregated_metrics(storage)
    assert metrics['document_count'] == 0
    assert metrics['processing']['completed_docs'] == 0
    assert metrics['errors']['total_errors'] == 0
    assert metrics['errors']['error_rate'] == 0.0

def test_get_aggregated_metrics(storage):
    """Test getting aggregated metrics with documents."""
    doc1_id = 'doc1'
    doc2_id = 'doc2'
    doc3_id = 'doc3'
    add_document(storage, doc_id=doc1_id)
    add_document(storage, doc_id=doc2_id)
    add_document(storage, doc_id=doc3_id)
    add_processing_step(storage, doc_id=doc1_id, step_name='extraction', status=ProcessingStatus.SUCCESS, details={'chars': 1000})
    add_processing_step(storage, doc_id=doc2_id, step_name='extraction', status=ProcessingStatus.FAILED, details={'error': 'timeout'})
    log_error_or_warning(storage, doc_id=doc1_id, level=LogLevel.WARNING, message='Low quality image')
    log_error_or_warning(storage, doc_id=doc2_id, level=LogLevel.ERROR, message='Processing failed')
    metrics = get_aggregated_metrics(storage)
    assert metrics['document_count'] == 3
    assert metrics['processing']['completed_docs'] == 1
    assert metrics['processing']['failed_docs'] == 1
    assert metrics['processing']['pending_docs'] == 1
    assert metrics['errors']['total_errors'] == 1
    assert metrics['errors']['total_warnings'] == 1
    assert metrics['errors']['error_rate'] == pytest.approx(0.33, rel=0.01, type_validation=True)

def test_get_aggregated_metrics_time_filtered(storage):
    """Test getting time-filtered aggregated metrics."""
    doc_id = 'doc1'
    add_document(storage, doc_id=doc_id)
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value = one_hour_ago
        add_processing_step(storage, doc_id=doc_id, step_name='step1', status=ProcessingStatus.SUCCESS)
        log_error_or_warning(storage, doc_id=doc_id, level=LogLevel.ERROR, message='Old error')
    recent_metrics = get_aggregated_metrics(storage, start_time=one_hour_ago)
    assert recent_metrics['processing']['completed_docs'] == 1
    assert recent_metrics['errors']['total_errors'] == 1
    future_metrics = get_aggregated_metrics(storage, start_time=datetime.now(timezone.utc))
    assert future_metrics['processing']['completed_docs'] == 0
    assert future_metrics['errors']['total_errors'] == 0

def test_get_real_time_status(storage):
    """Test getting real-time processing status."""
    doc_id = 'doc1'
    add_document(storage, doc_id=doc_id)
    add_processing_step(storage, doc_id=doc_id, step_name='extraction', status=ProcessingStatus.RUNNING)
    status = get_real_time_status(storage)
    assert status['active_processes'] == 1
    assert status['queued_documents'] == 0
    assert status['processing_documents'] == 1
    assert status['completed_documents'] == 0