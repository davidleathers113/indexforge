"""Performance and concurrency tests for integrated systems.

This module tests the performance characteristics and concurrent operation
of the core systems, including:
- Processing multiple documents simultaneously
- System behavior under load
- Resource usage monitoring
- Operation timing
"""

import asyncio
from datetime import UTC, datetime, timedelta
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
def managers(mock_storage):
    """Create all necessary managers for testing."""
    return {
        "lineage": LineageManager(),
        "error": ErrorLoggingManager(storage=mock_storage),
        "processing": ProcessingStepManager(storage=mock_storage),
        "source": SourceTracker(source_type="test_doc", config_dir="tests/fixtures/config"),
    }


async def process_document(doc_id: str, managers: dict, should_fail: bool = False):
    """Process a single document with all systems."""
    # Initialize document
    source_info = SourceInfo(
        source_id=f"test_{doc_id}",
        source_type="test_doc",
        location=f"/test/{doc_id}",
        metadata={"test": True},
    )

    await managers["lineage"].create_lineage(document_id=doc_id, source_info=source_info)

    # Add processing steps
    managers["processing"].add_step(
        doc_id=doc_id,
        step_name="initialization",
        status=ProcessingStatus.SUCCESS,
        details={"initialized": True},
    )

    if should_fail:
        managers["processing"].add_step(
            doc_id=doc_id,
            step_name="processing",
            status=ProcessingStatus.ERROR,
            error_message="Test failure",
        )
        managers["error"].log_error_or_warning(
            doc_id=doc_id, message="Processing failed", level=LogLevel.ERROR
        )
    else:
        managers["processing"].add_step(
            doc_id=doc_id,
            step_name="processing",
            status=ProcessingStatus.SUCCESS,
            details={"processed": True},
        )

    # Update lineage
    await managers["lineage"].update_lineage(
        document_id=doc_id,
        change_type=ChangeType.PROCESSED,
        metadata={"status": "error" if should_fail else "success"},
    )


@pytest.mark.asyncio
async def test_concurrent_document_processing(managers):
    """Test processing multiple documents concurrently."""
    # Create 10 documents, half will fail
    doc_ids = [str(uuid4()) for _ in range(10)]
    should_fail = [i % 2 == 0 for i in range(10)]

    # Process all documents concurrently
    tasks = [process_document(doc_id, managers, fail) for doc_id, fail in zip(doc_ids, should_fail, strict=False)]

    start_time = datetime.now(UTC)
    await asyncio.gather(*tasks)
    end_time = datetime.now(UTC)

    # Verify processing completed for all documents
    for doc_id, failed in zip(doc_ids, should_fail, strict=False):
        # Check processing steps
        steps = managers["processing"].get_steps(doc_id=doc_id)
        assert len(steps) == 2  # initialization + processing

        final_step = steps[-1]
        assert final_step.status == (ProcessingStatus.ERROR if failed else ProcessingStatus.SUCCESS)

        # Check error logs for failed documents
        if failed:
            logs = managers["error"].get_error_logs(doc_id=doc_id, log_level=LogLevel.ERROR)
            assert len(logs) == 1
            assert "Processing failed" in logs[0].message

        # Check lineage
        history = await managers["lineage"].get_document_history(doc_id)
        assert len(history) == 2  # creation + processing
        assert history[-1]["metadata"]["status"] == ("error" if failed else "success")

    # Verify reasonable processing time
    processing_time = end_time - start_time
    assert processing_time < timedelta(seconds=2)  # Should be quick


@pytest.mark.asyncio
async def test_system_under_load(managers):
    """Test system behavior under heavy load."""
    # Process 100 documents in batches of 10
    batch_size = 10
    total_docs = 100
    doc_ids = [str(uuid4()) for _ in range(total_docs)]

    start_time = datetime.now(UTC)

    # Process in batches
    for i in range(0, total_docs, batch_size):
        batch_ids = doc_ids[i : i + batch_size]
        tasks = [process_document(doc_id, managers, False) for doc_id in batch_ids]
        await asyncio.gather(*tasks)

    end_time = datetime.now(UTC)

    # Verify all documents were processed
    for doc_id in doc_ids:
        # Check processing steps exist
        steps = managers["processing"].get_steps(doc_id=doc_id)
        assert len(steps) == 2
        assert steps[-1].status == ProcessingStatus.SUCCESS

        # Check lineage exists
        history = await managers["lineage"].get_document_history(doc_id)
        assert len(history) == 2

    # Verify reasonable processing time
    # Should process at least 50 docs per second
    processing_time = end_time - start_time
    docs_per_second = total_docs / processing_time.total_seconds()
    assert docs_per_second >= 50


@pytest.mark.asyncio
async def test_error_recovery_under_load(managers):
    """Test error recovery while system is under load."""
    # Process 50 documents, all failing initially
    doc_ids = [str(uuid4()) for _ in range(50)]

    # First pass - all documents fail
    tasks = [process_document(doc_id, managers, True) for doc_id in doc_ids]
    await asyncio.gather(*tasks)

    # Verify all documents failed
    for doc_id in doc_ids:
        steps = managers["processing"].get_steps(doc_id=doc_id, status=ProcessingStatus.ERROR)
        assert len(steps) == 1

    # Second pass - retry all documents
    retry_tasks = [process_document(doc_id, managers, False) for doc_id in doc_ids]
    await asyncio.gather(*retry_tasks)

    # Verify all documents recovered
    for doc_id in doc_ids:
        # Check final status
        steps = managers["processing"].get_steps(doc_id=doc_id, status=ProcessingStatus.SUCCESS)
        assert len(steps) == 1  # Should have one successful step

        # Check lineage shows recovery
        history = await managers["lineage"].get_document_history(doc_id)
        assert history[-1]["metadata"]["status"] == "success"
