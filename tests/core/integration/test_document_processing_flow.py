"""Integration tests for the complete document processing flow.

This module tests the interactions between various core systems during document
processing, including:
- Processing steps system
- Error logging system
- Source tracking system
- Document lineage system
"""

from uuid import uuid4

import pytest

from src.core.lineage.base import ChangeType, SourceInfo
from src.core.lineage.manager import LineageManager
from src.core.monitoring.errors.lifecycle.manager import ErrorLoggingManager
from src.core.monitoring.errors.models.log_entry import LogLevel
from src.core.processing.steps.lifecycle.manager import ProcessingStepManager
from src.core.processing.steps.models.step import ProcessingStatus
from src.core.tracking.source.tracker import SourceTracker


@pytest.fixture
def source_tracker():
    """Create a source tracker for testing."""
    return SourceTracker(source_type="test_doc", config_dir="tests/fixtures/config")


@pytest.fixture
def error_logger(mock_storage):
    """Create an error logging manager for testing."""
    return ErrorLoggingManager(storage=mock_storage)


@pytest.fixture
def processing_manager(mock_storage):
    """Create a processing step manager for testing."""
    return ProcessingStepManager(storage=mock_storage)


@pytest.fixture
def lineage_manager():
    """Create a lineage manager for testing."""
    return LineageManager()


@pytest.mark.asyncio
async def test_end_to_end_document_processing(
    source_tracker,
    error_logger,
    processing_manager,
    lineage_manager,
    mock_storage,
):
    """Test complete document processing flow with all core systems.

    This test verifies that:
    1. Document source is properly tracked
    2. Processing steps are recorded
    3. Errors are logged appropriately
    4. Document lineage is maintained
    5. All systems interact correctly
    """
    # Setup test document
    doc_id = str(uuid4())
    source_info = SourceInfo(
        source_id="test123",
        source_type="test_doc",
        location="/test/path",
        metadata={"format": "text"},
    )

    # 1. Initialize document lineage
    lineage = await lineage_manager.create_lineage(document_id=doc_id, source_info=source_info)
    assert lineage is not None
    assert lineage.document_id == doc_id

    # 2. Record successful processing step
    processing_manager.add_step(
        doc_id=doc_id,
        step_name="text_extraction",
        status=ProcessingStatus.SUCCESS,
        details={"chars": 1000},
        metrics={"duration_ms": 150},
    )

    # Verify step was recorded
    steps = processing_manager.get_steps(doc_id=doc_id)
    assert len(steps) == 1
    assert steps[0].step_name == "text_extraction"
    assert steps[0].status == ProcessingStatus.SUCCESS

    # 3. Record a warning during processing
    error_logger.log_error_or_warning(
        doc_id=doc_id,
        message="Image quality below threshold",
        level=LogLevel.WARNING,
        metadata={"quality_score": 0.7},
    )

    # Verify warning was logged
    logs = error_logger.get_error_logs(doc_id=doc_id, log_level=LogLevel.WARNING)
    assert len(logs) == 1
    assert "Image quality" in logs[0].message

    # 4. Record failed processing step
    processing_manager.add_step(
        doc_id=doc_id,
        step_name="image_processing",
        status=ProcessingStatus.ERROR,
        error_message="Failed to process image",
        metrics={"duration_ms": 50},
    )

    # Verify error step was recorded
    steps = processing_manager.get_steps(doc_id=doc_id, status=ProcessingStatus.ERROR)
    assert len(steps) == 1
    assert steps[0].step_name == "image_processing"

    # 5. Log error for failed step
    error_logger.log_error_or_warning(
        doc_id=doc_id,
        message="Image processing failed",
        level=LogLevel.ERROR,
        metadata={"step": "image_processing"},
    )

    # Verify error was logged
    logs = error_logger.get_error_logs(doc_id=doc_id, log_level=LogLevel.ERROR)
    assert len(logs) == 1
    assert "Image processing failed" in logs[0].message

    # 6. Update document lineage
    await lineage_manager.update_lineage(
        document_id=doc_id,
        change_type=ChangeType.PROCESSED,
        metadata={"process": "image_processing", "status": "error"},
    )

    # Verify lineage was updated
    history = await lineage_manager.get_document_history(doc_id)
    assert len(history) == 2  # Initial creation + update
    assert history[-1]["change_type"] == ChangeType.PROCESSED

    # 7. Verify source tracking
    schema = source_tracker.get_schema()
    assert schema["class"] == "TestDocDocument"
    assert "source_metadata" in schema["properties"]


@pytest.mark.asyncio
async def test_cross_system_error_handling(
    source_tracker,
    error_logger,
    processing_manager,
    lineage_manager,
    mock_storage,
):
    """Test error handling across system boundaries.

    This test verifies that:
    1. Errors propagate correctly between systems
    2. Error states are consistently recorded
    3. Document lineage reflects error conditions
    4. Error recovery paths work correctly
    """
    doc_id = str(uuid4())

    # 1. Initialize document
    lineage = await lineage_manager.create_lineage(
        document_id=doc_id,
        source_info=SourceInfo(source_id="test456", source_type="test_doc", location="/test/path"),
    )

    # 2. Simulate cascading error
    # First, record processing error
    processing_manager.add_step(
        doc_id=doc_id,
        step_name="validation",
        status=ProcessingStatus.ERROR,
        error_message="Schema validation failed",
    )

    # Log the error
    error_logger.log_error_or_warning(
        doc_id=doc_id,
        message="Validation error in schema",
        level=LogLevel.ERROR,
        metadata={"validation": "failed"},
    )

    # Update lineage
    await lineage_manager.update_lineage(
        document_id=doc_id,
        change_type=ChangeType.PROCESSED,
        metadata={"error": "validation_failed"},
    )

    # 3. Verify error state consistency
    # Check processing status
    steps = processing_manager.get_steps(doc_id=doc_id, status=ProcessingStatus.ERROR)
    assert len(steps) == 1
    assert steps[0].step_name == "validation"

    # Check error logs
    logs = error_logger.get_error_logs(doc_id=doc_id, log_level=LogLevel.ERROR)
    assert len(logs) == 1
    assert "Validation error" in logs[0].message

    # Check lineage
    history = await lineage_manager.get_document_history(doc_id)
    assert len(history) == 2
    assert "validation_failed" in history[-1]["metadata"]["error"]

    # 4. Test error recovery
    # Record recovery step
    processing_manager.add_step(
        doc_id=doc_id,
        step_name="validation_retry",
        status=ProcessingStatus.SUCCESS,
        details={"retry": True},
    )

    # Update lineage for recovery
    await lineage_manager.update_lineage(
        document_id=doc_id, change_type=ChangeType.PROCESSED, metadata={"recovery": "successful"}
    )

    # Verify recovery state
    steps = processing_manager.get_steps(doc_id=doc_id, status=ProcessingStatus.SUCCESS)
    assert len(steps) == 1
    assert steps[0].step_name == "validation_retry"

    history = await lineage_manager.get_document_history(doc_id)
    assert len(history) == 3
    assert history[-1]["metadata"]["recovery"] == "successful"
