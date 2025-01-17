"""Tests for document processing step tracking."""

import pytest

from src.connectors.direct_documentation_indexing.source_tracking import (
    add_document,
    add_processing_step,
    get_processing_steps,
)
from src.connectors.direct_documentation_indexing.source_tracking.storage import LineageStorage
from src.core.processing.steps.models.step import ProcessingStatus


@pytest.fixture
def temp_lineage_dir(tmp_path):
    """Create a temporary directory for test lineage data."""
    return tmp_path / "lineage"


@pytest.fixture
def storage(temp_lineage_dir):
    """Create a LineageStorage instance."""
    return LineageStorage(str(temp_lineage_dir))


def test_add_processing_step(storage):
    """Test adding a processing step."""
    doc_id = "test_doc"
    add_document(storage, doc_id=doc_id)
    step_name = "text_extraction"
    status = ProcessingStatus.SUCCESS
    details = {"chars": 1000}
    add_processing_step(storage, doc_id=doc_id, step_name=step_name, status=status, details=details)
    steps = get_processing_steps(storage, doc_id)
    assert len(steps) == 1
    assert steps[0].step_name == step_name
    assert steps[0].status == status
    assert steps[0].details == details


def test_add_processing_step_invalid_status(storage):
    """Test adding a processing step with invalid status."""
    doc_id = "test_doc"
    add_document(storage, doc_id=doc_id)
    with pytest.raises(ValueError):
        add_processing_step(storage, doc_id=doc_id, step_name="test", status="invalid_status")


def test_add_processing_step_missing_doc(storage):
    """Test adding a processing step for non-existent document."""
    with pytest.raises(ValueError):
        add_processing_step(
            storage, doc_id="non_existent", step_name="test", status=ProcessingStatus.SUCCESS
        )


def test_get_processing_steps(storage):
    """Test getting processing steps."""
    doc_id = "test_doc"
    add_document(storage, doc_id=doc_id)
    steps_data = [
        ("step1", ProcessingStatus.SUCCESS, {"result": "ok"}),
        ("step2", ProcessingStatus.FAILED, {"error": "timeout"}),
        ("step3", ProcessingStatus.RUNNING, {}),
    ]
    for step_name, status, details in steps_data:
        add_processing_step(
            storage, doc_id=doc_id, step_name=step_name, status=status, details=details
        )
    steps = get_processing_steps(storage, doc_id)
    assert len(steps) == len(steps_data)
    for step, (name, status, details) in zip(steps, steps_data, strict=False):
        assert step.step_name == name
        assert step.status == status
        assert step.details == details


def test_processing_steps_persistence(temp_lineage_dir):
    """Test persistence of processing steps."""
    storage1 = LineageStorage(str(temp_lineage_dir))
    doc_id = "test_doc"
    add_document(storage1, doc_id=doc_id)
    add_processing_step(storage1, doc_id=doc_id, step_name="test", status=ProcessingStatus.SUCCESS)
    storage2 = LineageStorage(str(temp_lineage_dir))
    steps = get_processing_steps(storage2, doc_id)
    assert len(steps) == 1
    assert steps[0].step_name == "test"
    assert steps[0].status == ProcessingStatus.SUCCESS
