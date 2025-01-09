"""Tests for document lineage tracking functionality."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
import pytest
from src.connectors.direct_documentation_indexing.source_tracking import add_processing_step, get_aggregated_metrics, get_error_logs, get_processing_steps, get_real_time_status, log_error_or_warning, validate_lineage_relationships
from src.connectors.direct_documentation_indexing.source_tracking.document_operations import add_document
from src.connectors.direct_documentation_indexing.source_tracking.enums import LogLevel, ProcessingStatus, TransformationType
from src.connectors.direct_documentation_indexing.source_tracking.lineage_operations import add_derivation, get_derivation_chain
from src.connectors.direct_documentation_indexing.source_tracking.models import DocumentLineage, Transformation
from src.connectors.direct_documentation_indexing.source_tracking.storage import LineageStorage
from src.connectors.direct_documentation_indexing.source_tracking.transformation_manager import get_transformation_history, record_transformation

@pytest.fixture
def temp_lineage_dir(tmp_path):
    """Create a temporary directory for test lineage data."""
    return tmp_path / 'lineage'

@pytest.fixture
def storage(temp_lineage_dir):
    """Create a LineageStorage instance."""
    return LineageStorage(str(temp_lineage_dir))

def test_add_document(storage):
    """Test adding a document to lineage tracking."""
    doc_id = 'test_doc'
    metadata = {'type': 'pdf', 'pages': 10}
    add_document(storage, doc_id=doc_id, metadata=metadata)
    lineage = storage.get_lineage(doc_id)
    assert lineage is not None
    assert lineage.doc_id == doc_id
    assert lineage.metadata == metadata

def test_record_transformation(storage):
    """Test recording a document transformation."""
    doc_id = 'test_doc'
    add_document(storage, doc_id=doc_id)
    transform_type = TransformationType.TEXT_EXTRACTION
    description = 'Extract text from PDF'
    parameters = {'engine': 'tesseract'}
    record_transformation(storage, doc_id=doc_id, transform_type=transform_type, description=description, parameters=parameters)
    lineage = storage.get_lineage(doc_id)
    history = get_transformation_history(lineage, transform_type)
    assert len(history) == 1
    assert history[0].transform_type == transform_type
    assert history[0].description == description
    assert history[0].parameters == parameters

def test_add_derivation(storage):
    """Test adding document derivation."""
    parent_id = 'parent_doc'
    derived_id = 'derived_doc'
    add_document(storage, doc_id=parent_id)
    add_document(storage, doc_id=derived_id, parent_ids=[parent_id])
    chain = get_derivation_chain(storage, derived_id)
    chain_ids = [doc.doc_id for doc in chain]
    assert parent_id in chain_ids
    parent = storage.get_lineage(parent_id)
    derived = storage.get_lineage(derived_id)
    assert derived_id in parent.children
    assert parent_id in derived.parents

def test_get_transformation_history(storage):
    """Test getting transformation history for a document."""
    doc_id = 'test_doc'
    add_document(storage, doc_id=doc_id)
    transformations = [(TransformationType.TEXT_EXTRACTION, 'Extract text'), (TransformationType.CONTENT_ENRICHMENT, 'Enrich content'), (TransformationType.METADATA_UPDATE, 'Update metadata')]
    for transform_type, description in transformations:
        record_transformation(storage, doc_id=doc_id, transform_type=transform_type, description=description)
    lineage = storage.get_lineage(doc_id)
    history = get_transformation_history(lineage)
    assert len(history) == len(transformations)
    filtered = get_transformation_history(lineage, TransformationType.TEXT_EXTRACTION)
    assert len(filtered) == 1
    assert filtered[0].transform_type == TransformationType.TEXT_EXTRACTION

def test_get_derivation_chain(storage):
    """Test getting document derivation chain."""
    doc_ids = ['doc1', 'doc2', 'doc3', 'doc4']
    add_document(storage, doc_id=doc_ids[0])
    for i in range(1, len(doc_ids)):
        add_document(storage, doc_id=doc_ids[i], parent_ids=[doc_ids[i - 1]])
    chain = get_derivation_chain(storage, doc_ids[-1])
    assert len(chain) == len(doc_ids)
    chain_ids = [doc.doc_id for doc in chain]
    for i in range(len(doc_ids)):
        assert chain_ids[i] == doc_ids[i]
    for i in range(len(doc_ids) - 1):
        parent = storage.get_lineage(doc_ids[i])
        child = storage.get_lineage(doc_ids[i + 1])
        assert doc_ids[i + 1] in parent.children
        assert doc_ids[i] in child.parents

def test_validate_lineage_circular(storage):
    """Test detection of circular lineage relationships."""
    doc_ids = ['doc1', 'doc2', 'doc3']
    add_document(storage, doc_id=doc_ids[0])
    add_document(storage, doc_id=doc_ids[1], parent_ids=[doc_ids[0]])
    add_document(storage, doc_id=doc_ids[2], parent_ids=[doc_ids[1]])
    with pytest.raises(ValueError) as exc_info:
        storage.update_document_lineage(doc_ids[0], {'parents': [doc_ids[2]]})
    assert 'circular' in str(exc_info.value).lower()
    for i in range(len(doc_ids) - 1):
        parent = storage.get_lineage(doc_ids[i])
        child = storage.get_lineage(doc_ids[i + 1])
        assert doc_ids[i + 1] in parent.children
        assert doc_ids[i] in child.parents

def test_validate_lineage_missing_refs(storage):
    """Test validation of missing references."""
    doc_id = 'test_doc'
    missing_id = 'missing_doc'
    add_document(storage, doc_id=doc_id)
    storage.lineage_data[doc_id].parents.append(missing_id)
    errors = validate_lineage_relationships(storage.get_all_lineage())
    assert any(('missing' in error.lower() for error in errors))

def test_persistence(temp_lineage_dir):
    """Test persistence of document transformations."""
    storage1 = LineageStorage(str(temp_lineage_dir))
    doc_id = 'test_doc'
    add_document(storage1, doc_id=doc_id)
    record_transformation(storage1, doc_id=doc_id, transform_type=TransformationType.SPLIT, metadata={'chunks': 3})
    storage2 = LineageStorage(str(temp_lineage_dir))
    lineage = storage2.get_lineage(doc_id)
    if not lineage:
        raise ValueError(f'Document {doc_id} not found in storage2')
    history = get_transformation_history(lineage)
    assert len(history) == 1
    assert history[0].transform_type == TransformationType.SPLIT
    assert history[0].metadata == {'chunks': 3}

def test_error_handling(storage):
    """Test error handling in lineage operations."""
    doc_id = 'test_doc'
    add_document(storage, doc_id=doc_id)
    with pytest.raises(ValueError):
        record_transformation(storage, doc_id=doc_id, transform_type='invalid_type')
    with pytest.raises(ValueError):
        record_transformation(storage, doc_id='non_existent', transform_type=TransformationType.TEXT_EXTRACTION)

def test_add_processing_step(storage):
    """Test adding a processing step."""
    doc_id = 'test_doc'
    add_document(storage, doc_id=doc_id)
    step_name = 'text_extraction'
    status = ProcessingStatus.SUCCESS
    details = {'chars': 1000}
    add_processing_step(storage, doc_id=doc_id, step_name=step_name, status=status, details=details)
    steps = get_processing_steps(storage, doc_id)
    assert len(steps) == 1
    assert steps[0].step_name == step_name
    assert steps[0].status == status
    assert steps[0].details == details

def test_add_processing_step_invalid_status(storage):
    """Test adding a processing step with invalid status."""
    doc_id = 'test_doc'
    add_document(storage, doc_id=doc_id)
    with pytest.raises(ValueError):
        add_processing_step(storage, doc_id=doc_id, step_name='test', status='invalid_status')

def test_add_processing_step_missing_doc(storage):
    """Test adding a processing step for non-existent document."""
    with pytest.raises(ValueError):
        add_processing_step(storage, doc_id='non_existent', step_name='test', status=ProcessingStatus.SUCCESS)

def test_get_processing_steps(storage):
    """Test getting processing steps."""
    doc_id = 'test_doc'
    add_document(storage, doc_id=doc_id)
    steps_data = [('step1', ProcessingStatus.SUCCESS, {'result': 'ok'}), ('step2', ProcessingStatus.FAILED, {'error': 'timeout'}), ('step3', ProcessingStatus.RUNNING, {})]
    for step_name, status, details in steps_data:
        add_processing_step(storage, doc_id=doc_id, step_name=step_name, status=status, details=details)
    steps = get_processing_steps(storage, doc_id)
    assert len(steps) == len(steps_data)
    for step, (name, status, details) in zip(steps, steps_data):
        assert step.step_name == name
        assert step.status == status
        assert step.details == details

def test_processing_steps_persistence(temp_lineage_dir):
    """Test persistence of processing steps."""
    storage1 = LineageStorage(str(temp_lineage_dir))
    doc_id = 'test_doc'
    add_document(storage1, doc_id=doc_id)
    add_processing_step(storage1, doc_id=doc_id, step_name='test', status=ProcessingStatus.SUCCESS)
    storage2 = LineageStorage(str(temp_lineage_dir))
    steps = get_processing_steps(storage2, doc_id)
    assert len(steps) == 1
    assert steps[0].step_name == 'test'
    assert steps[0].status == ProcessingStatus.SUCCESS

def test_log_error_or_warning(storage):
    """Test logging errors and warnings."""
    doc_id = 'test_doc'
    add_document(storage, doc_id=doc_id)
    log_error_or_warning(storage, doc_id=doc_id, level=LogLevel.ERROR, message='Test error')
    logs = storage.get_lineage(doc_id).error_logs
    assert len(logs) == 1
    assert logs[0].log_level == LogLevel.ERROR
    assert logs[0].message == 'Test error'

def test_log_error_or_warning_invalid_level(storage):
    """Test logging with invalid level."""
    doc_id = 'test_doc'
    add_document(storage, doc_id=doc_id)
    with pytest.raises(ValueError):
        log_error_or_warning(storage, doc_id=doc_id, level='invalid_level', message='Test')

def test_log_error_or_warning_missing_doc(storage):
    """Test logging for non-existent document."""
    with pytest.raises(ValueError):
        log_error_or_warning(storage, doc_id='non_existent', level=LogLevel.ERROR, message='Test')

def test_get_error_logs_filtered(storage):
    """Test filtering error logs by level."""
    doc_id = 'test_doc'
    add_document(storage, doc_id=doc_id)
    log_error_or_warning(storage, doc_id=doc_id, level=LogLevel.ERROR, message='Test error')
    log_error_or_warning(storage, doc_id=doc_id, level=LogLevel.WARNING, message='Test warning')
    error_logs = [log for log in storage.get_lineage(doc_id).error_logs if log.log_level == LogLevel.ERROR]
    warning_logs = [log for log in storage.get_lineage(doc_id).error_logs if log.log_level == LogLevel.WARNING]
    assert len(error_logs) == 1
    assert len(warning_logs) == 1
    assert error_logs[0].message == 'Test error'
    assert warning_logs[0].message == 'Test warning'

def test_get_error_logs_time_filtered(storage):
    """Test filtering error logs by time range."""
    doc_id = 'test_doc'
    add_document(storage, doc_id=doc_id)
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(hours=2)
    recent_time = now - timedelta(minutes=30)
    log_error_or_warning(storage, doc_id=doc_id, level=LogLevel.ERROR, message='Old error', timestamp=old_time)
    log_error_or_warning(storage, doc_id=doc_id, level=LogLevel.ERROR, message='Recent error', timestamp=recent_time)
    recent_logs = [log for log in storage.get_lineage(doc_id).error_logs if log.timestamp >= now - timedelta(hours=1)]
    assert len(recent_logs) == 1
    assert recent_logs[0].message == 'Recent error'

def test_error_logs_persistence(temp_lineage_dir):
    """Test persistence of error logs."""
    storage1 = LineageStorage(str(temp_lineage_dir))
    doc_id = 'test_doc'
    add_document(storage1, doc_id=doc_id)
    log_error_or_warning(storage1, doc_id=doc_id, level=LogLevel.ERROR, message='Test error')
    storage2 = LineageStorage(str(temp_lineage_dir))
    lineage = storage2.get_lineage(doc_id)
    assert lineage is not None, f'Document {doc_id} not found in storage2'
    logs = lineage.error_logs
    assert len(logs) == 1
    assert logs[0].log_level == LogLevel.ERROR
    assert logs[0].message == 'Test error'