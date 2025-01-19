"""Cross-package validation tests.

This module tests the validation and integrity checks across package boundaries,
ensuring that:
- Data consistency is maintained across systems
- Validation rules are properly enforced
- Cross-package dependencies work correctly
- Error conditions are handled appropriately
"""

from uuid import uuid4

import pytest

from src.core.errors import ValidationError
from src.core.lineage.base import ChangeType, SourceInfo
from src.core.lineage.manager import LineageManager
from src.core.monitoring.errors.lifecycle.manager import ErrorLoggingManager
from src.core.monitoring.errors.models.log_entry import LogLevel
from src.core.processing.steps.lifecycle.manager import ProcessingStepManager
from src.core.processing.steps.models.step import ProcessingStatus
from src.core.tracking.source.tracker import SourceTracker


@pytest.fixture
def managers(mock_storage):
    """Create all necessary managers for testing."""
    return {
        "lineage": LineageManager(),
        "error": ErrorLoggingManager(storage=mock_storage),
        "processing": ProcessingStepManager(storage=mock_storage),
        "source": SourceTracker(source_type="test_doc", config_dir="tests/fixtures/config"),
    }


@pytest.mark.asyncio
async def test_cross_package_data_consistency(managers):
    """Test data consistency across different packages."""
    doc_id = str(uuid4())

    # 1. Create document with source info
    source_info = SourceInfo(
        source_id="test123",
        source_type="test_doc",
        location="/test/path",
        metadata={"format": "text"},
    )

    lineage = await managers["lineage"].create_lineage(document_id=doc_id, source_info=source_info)
    assert lineage is not None
    assert lineage.document_id == doc_id

    # 2. Add processing step
    managers["processing"].add_step(
        doc_id=doc_id,
        step_name="validation",
        status=ProcessingStatus.SUCCESS,
        details={"validated": True},
    )

    # 3. Verify consistency across packages
    # Check lineage
    history = await managers["lineage"].get_document_history(doc_id)
    assert len(history) == 1
    assert history[0]["source_info"]["source_id"] == "test123"

    # Check processing
    steps = managers["processing"].get_steps(doc_id=doc_id)
    assert len(steps) == 1
    assert steps[0].step_name == "validation"

    # Check source tracking
    schema = managers["source"].get_schema()
    assert schema["class"] == "TestDocDocument"


@pytest.mark.asyncio
async def test_validation_rule_enforcement(managers):
    """Test that validation rules are enforced across packages."""
    doc_id = str(uuid4())

    # 1. Test invalid source info
    with pytest.raises(ValidationError):
        await managers["lineage"].create_lineage(
            document_id=doc_id,
            source_info=SourceInfo(
                source_id="",  # Invalid empty source ID
                source_type="test_doc",
                location="/test/path",
            ),
        )

    # 2. Test invalid processing step
    with pytest.raises(ValueError):
        managers["processing"].add_step(
            doc_id=doc_id, step_name="", status=ProcessingStatus.SUCCESS  # Invalid empty step name
        )

    # 3. Test invalid error log
    with pytest.raises(ValueError):
        managers["error"].log_error_or_warning(
            doc_id=doc_id, message="", level=LogLevel.ERROR  # Invalid empty message
        )


@pytest.mark.asyncio
async def test_cross_package_error_propagation(managers):
    """Test error propagation across package boundaries."""
    doc_id = str(uuid4())

    # 1. Initialize document
    source_info = SourceInfo(source_id="test123", source_type="test_doc", location="/test/path")
    await managers["lineage"].create_lineage(document_id=doc_id, source_info=source_info)

    # 2. Simulate validation error in processing
    managers["processing"].add_step(
        doc_id=doc_id,
        step_name="validation",
        status=ProcessingStatus.ERROR,
        error_message="Validation failed",
    )

    # Error should propagate to error logging
    managers["error"].log_error_or_warning(
        doc_id=doc_id,
        message="Validation error occurred",
        level=LogLevel.ERROR,
        metadata={"step": "validation"},
    )

    # Error should be reflected in lineage
    await managers["lineage"].update_lineage(
        document_id=doc_id,
        change_type=ChangeType.PROCESSED,
        metadata={"error": "validation_failed"},
    )

    # 3. Verify error state consistency
    # Check processing status
    steps = managers["processing"].get_steps(doc_id=doc_id, status=ProcessingStatus.ERROR)
    assert len(steps) == 1
    assert steps[0].error_message == "Validation failed"

    # Check error logs
    logs = managers["error"].get_error_logs(doc_id=doc_id, log_level=LogLevel.ERROR)
    assert len(logs) == 1
    assert logs[0].metadata["step"] == "validation"

    # Check lineage
    history = await managers["lineage"].get_document_history(doc_id)
    assert history[-1]["metadata"]["error"] == "validation_failed"


@pytest.mark.asyncio
async def test_cross_package_dependencies(managers):
    """Test that cross-package dependencies work correctly."""
    doc_id = str(uuid4())

    # 1. Test lineage dependency on source tracking
    source_info = SourceInfo(source_id="test123", source_type="test_doc", location="/test/path")
    lineage = await managers["lineage"].create_lineage(document_id=doc_id, source_info=source_info)
    assert lineage is not None
    assert lineage.document_id == doc_id

    # Source type should match schema
    schema = managers["source"].get_schema()
    assert source_info.source_type in schema["class"].lower()

    # 2. Test processing dependency on lineage
    managers["processing"].add_step(
        doc_id=doc_id, step_name="processing", status=ProcessingStatus.SUCCESS
    )

    # Step should be reflected in lineage
    await managers["lineage"].update_lineage(document_id=doc_id, change_type=ChangeType.PROCESSED)

    history = await managers["lineage"].get_document_history(doc_id)
    assert len(history) == 2  # Creation + processing

    # 3. Test error logging dependency on processing
    managers["error"].log_error_or_warning(
        doc_id=doc_id, message="Test warning", level=LogLevel.WARNING
    )

    # Warning should not affect processing status
    steps = managers["processing"].get_steps(doc_id=doc_id, status=ProcessingStatus.SUCCESS)
    assert len(steps) == 1
