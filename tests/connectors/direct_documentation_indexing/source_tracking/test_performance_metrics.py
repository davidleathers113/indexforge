"""Tests for performance metrics functionality."""
from datetime import datetime, timedelta, timezone

import pytest

from src.connectors.direct_documentation_indexing.source_tracking import (
    add_processing_step,
    get_aggregated_metrics,
    get_real_time_status,
)
from src.connectors.direct_documentation_indexing.source_tracking.document_operations import (
    add_document,
)
from src.connectors.direct_documentation_indexing.source_tracking.enums import ProcessingStatus
from src.connectors.direct_documentation_indexing.source_tracking.storage import LineageStorage


@pytest.fixture
def temp_lineage_dir(tmp_path):
    """Create a temporary directory for test lineage data."""
    return tmp_path / 'lineage'

@pytest.fixture
def storage(temp_lineage_dir):
    """Create a LineageStorage instance."""
    return LineageStorage(str(temp_lineage_dir))

def test_real_time_status(storage):
    """Test getting real-time status of document processing."""
    doc_id = 'test_doc'
    add_document(storage, doc_id=doc_id)
    add_processing_step(storage, doc_id=doc_id, step_name='extract', status=ProcessingStatus.SUCCESS)
    add_processing_step(storage, doc_id=doc_id, step_name='transform', status=ProcessingStatus.IN_PROGRESS)
    status = get_real_time_status(storage, doc_id)
    assert status['current_step'] == 'transform'
    assert status['status'] == ProcessingStatus.IN_PROGRESS
    assert status['completed_documents'] == 1
    assert status['active_documents'] == 1

def test_aggregated_metrics(storage):
    """Test getting aggregated metrics for document processing."""
    doc_id = 'test_doc'
    add_document(storage, doc_id=doc_id)
    add_processing_step(storage, doc_id=doc_id, step_name='process', status=ProcessingStatus.SUCCESS, details={'metrics': {'processing_time': 100, 'memory_usage': 500}})
    add_processing_step(storage, doc_id=doc_id, step_name='process', status=ProcessingStatus.SUCCESS, details={'metrics': {'processing_time': 150, 'memory_usage': 600}})
    metrics = get_aggregated_metrics(storage.get_all_lineage())
    assert metrics['processing']['average_time'] == 125
    assert metrics['resources']['peak_memory_mb'] == 600

def test_real_time_status_with_errors(storage):
    """Test real-time status with error conditions."""
    doc_id = 'test_doc'
    add_document(storage, doc_id=doc_id)
    add_processing_step(storage, doc_id=doc_id, step_name='process', status=ProcessingStatus.FAILED, details={'error_message': 'Test error'})
    status = get_real_time_status(storage, doc_id)
    assert status['status'] == ProcessingStatus.FAILED
    assert status['error_rate'] > 0
    assert status['success_rate'] == 0

def test_metrics_persistence(temp_lineage_dir):
    """Test persistence of performance metrics."""
    storage1 = LineageStorage(str(temp_lineage_dir))
    doc_id = 'test_doc'
    add_document(storage1, doc_id=doc_id)
    add_processing_step(storage1, doc_id=doc_id, step_name='process', status=ProcessingStatus.SUCCESS, details={'metrics': {'processing_time': 100}})
    storage2 = LineageStorage(str(temp_lineage_dir))
    metrics = get_aggregated_metrics(storage2.get_all_lineage())
    assert metrics['processing']['average_time'] == 100

def test_metrics_with_multiple_documents(storage):
    """Test metrics tracking for multiple documents."""
    doc_ids = ['doc1', 'doc2']
    metrics_data = {'doc1': {'processing_time': 100, 'memory_usage': 500}, 'doc2': {'processing_time': 200, 'memory_usage': 700}}
    for doc_id in doc_ids:
        add_document(storage, doc_id=doc_id)
        add_processing_step(storage, doc_id=doc_id, step_name='process', status=ProcessingStatus.SUCCESS, details={'metrics': metrics_data[doc_id]})
    metrics = get_aggregated_metrics(storage.get_all_lineage())
    assert metrics['processing']['average_time'] == 150
    assert metrics['resources']['peak_memory_mb'] == 700

def test_metrics_with_time_range(storage):
    """Test metrics aggregation within time range."""
    doc_id = 'test_doc'
    add_document(storage, doc_id=doc_id)
    now = datetime.now(timezone.utc)
    add_processing_step(storage, doc_id=doc_id, step_name='process1', status=ProcessingStatus.SUCCESS, details={'metrics': {'processing_time': 100}}, timestamp=now - timedelta(hours=2))
    add_processing_step(storage, doc_id=doc_id, step_name='process2', status=ProcessingStatus.SUCCESS, details={'metrics': {'processing_time': 200}}, timestamp=now - timedelta(hours=1))
    metrics = get_aggregated_metrics(storage.get_all_lineage(), start_time=now - timedelta(hours=1))
    assert metrics['processing']['average_time'] == 200

def test_real_time_status_updates(storage):
    """Test real-time status updates during processing."""
    doc_id = 'test_doc'
    add_document(storage, doc_id=doc_id)
    add_processing_step(storage, doc_id=doc_id, step_name='step1', status=ProcessingStatus.SUCCESS)
    status = get_real_time_status(storage, doc_id)
    assert status['current_step'] == 'step1'
    assert status['status'] == ProcessingStatus.SUCCESS
    add_processing_step(storage, doc_id=doc_id, step_name='step2', status=ProcessingStatus.IN_PROGRESS)
    status = get_real_time_status(storage, doc_id)
    assert status['current_step'] == 'step2'
    assert status['status'] == ProcessingStatus.IN_PROGRESS