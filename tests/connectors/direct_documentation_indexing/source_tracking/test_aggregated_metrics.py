"""Tests for aggregated metrics functionality."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from src.connectors.direct_documentation_indexing.source_tracking import (
    add_processing_step,
    get_aggregated_metrics,
    get_real_time_status,
    log_error_or_warning,
)
from src.connectors.direct_documentation_indexing.source_tracking.document_operations import (
    add_document,
)
from src.connectors.direct_documentation_indexing.source_tracking.enums import (
    LogLevel,
    ProcessingStatus,
)
from src.connectors.direct_documentation_indexing.source_tracking.storage import LineageStorage


@pytest.fixture
def setup_test_documents(storage):
    """Helper fixture to set up test documents with various states."""
    docs = {
        "doc1": {"status": ProcessingStatus.SUCCESS, "has_warning": True},
        "doc2": {"status": ProcessingStatus.FAILED, "has_error": True},
        "doc3": {"status": ProcessingStatus.PENDING},
    }

    for doc_id, config in docs.items():
        add_document(storage, doc_id=doc_id)
        if "status" in config:
            add_processing_step(
                storage,
                doc_id=doc_id,
                step_name="extraction",
                status=config["status"],
                details=(
                    {"chars": 1000}
                    if config["status"] == ProcessingStatus.SUCCESS
                    else {"error": "timeout"}
                ),
            )
        if config.get("has_warning"):
            log_error_or_warning(
                storage, doc_id=doc_id, level=LogLevel.WARNING, message="Low quality image"
            )
        if config.get("has_error"):
            log_error_or_warning(
                storage, doc_id=doc_id, level=LogLevel.ERROR, message="Processing failed"
            )

    return docs


def test_get_aggregated_metrics_empty(storage):
    """Test getting aggregated metrics with no documents."""
    metrics = get_aggregated_metrics(storage)
    assert metrics["document_count"] == 0, "Empty storage should have zero documents"
    assert (
        metrics["processing"]["completed_docs"] == 0
    ), "Empty storage should have no completed docs"
    assert metrics["errors"]["total_errors"] == 0, "Empty storage should have no errors"
    assert metrics["errors"]["error_rate"] == 0.0, "Empty storage should have zero error rate"


def test_get_aggregated_metrics(storage, setup_test_documents):
    """Test getting aggregated metrics with documents in various states."""
    metrics = get_aggregated_metrics(storage)

    # Document counts
    assert metrics["document_count"] == 3, "Should have exactly 3 documents"
    assert metrics["processing"]["completed_docs"] == 1, "Should have 1 completed document"
    assert metrics["processing"]["failed_docs"] == 1, "Should have 1 failed document"
    assert metrics["processing"]["pending_docs"] == 1, "Should have 1 pending document"

    # Error metrics
    assert metrics["errors"]["total_errors"] == 1, "Should have 1 error"
    assert metrics["errors"]["total_warnings"] == 1, "Should have 1 warning"
    assert metrics["errors"]["error_rate"] == pytest.approx(
        0.33, rel=0.01
    ), "Error rate should be ~33%"


def test_get_aggregated_metrics_time_filtered(storage):
    """Test getting time-filtered aggregated metrics."""
    doc_id = "doc1"
    add_document(storage, doc_id=doc_id)

    # Create events at different times
    one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
    with patch("datetime.datetime") as mock_datetime:
        mock_datetime.now.return_value = one_hour_ago
        add_processing_step(
            storage, doc_id=doc_id, step_name="step1", status=ProcessingStatus.SUCCESS
        )
        log_error_or_warning(storage, doc_id=doc_id, level=LogLevel.ERROR, message="Old error")

    # Test recent metrics
    recent_metrics = get_aggregated_metrics(storage, start_time=one_hour_ago)
    assert (
        recent_metrics["processing"]["completed_docs"] == 1
    ), "Should include events from last hour"
    assert recent_metrics["errors"]["total_errors"] == 1, "Should include errors from last hour"

    # Test future metrics
    future_metrics = get_aggregated_metrics(storage, start_time=datetime.now(UTC))
    assert future_metrics["processing"]["completed_docs"] == 0, "Should exclude past events"
    assert future_metrics["errors"]["total_errors"] == 0, "Should exclude past errors"


def test_get_real_time_status(storage):
    """Test getting real-time processing status."""
    # Add documents in different states
    docs = {
        "doc1": ProcessingStatus.RUNNING,
        "doc2": ProcessingStatus.QUEUED,
        "doc3": ProcessingStatus.SUCCESS,
        "doc4": ProcessingStatus.RUNNING,
    }

    for doc_id, status in docs.items():
        add_document(storage, doc_id=doc_id)
        add_processing_step(storage, doc_id=doc_id, step_name="extraction", status=status)

    status = get_real_time_status(storage)
    assert status["active_processes"] == 2, "Should have 2 active processes"
    assert status["queued_documents"] == 1, "Should have 1 queued document"
    assert status["processing_documents"] == 2, "Should have 2 processing documents"
    assert status["completed_documents"] == 1, "Should have 1 completed document"


def test_metric_calculation_edge_cases(storage):
    """Test metric calculation with edge cases."""
    # Test with zero documents
    metrics = get_aggregated_metrics(storage)
    assert metrics["errors"]["error_rate"] == 0.0, "Error rate should be 0 with no documents"

    # Test with only errors
    doc_id = "error_doc"
    add_document(storage, doc_id=doc_id)
    add_processing_step(storage, doc_id=doc_id, step_name="step1", status=ProcessingStatus.FAILED)
    log_error_or_warning(storage, doc_id=doc_id, level=LogLevel.ERROR, message="Error")

    metrics = get_aggregated_metrics(storage)
    assert metrics["errors"]["error_rate"] == 1.0, "Error rate should be 1.0 with only errors"

    # Test with large numbers
    for i in range(1000):
        doc_id = f"doc_{i}"
        add_document(storage, doc_id=doc_id)
        add_processing_step(
            storage, doc_id=doc_id, step_name="step1", status=ProcessingStatus.SUCCESS
        )

    metrics = get_aggregated_metrics(storage)
    assert metrics["document_count"] == 1001, "Should handle large number of documents"
    assert 0.0 <= metrics["errors"]["error_rate"] <= 1.0, "Error rate should be between 0 and 1"


def test_metric_persistence(storage, temp_lineage_dir):
    """Test that metrics persist across storage instances."""
    # Add data with first storage instance
    doc_id = "doc1"
    add_document(storage, doc_id=doc_id)
    add_processing_step(storage, doc_id=doc_id, step_name="step1", status=ProcessingStatus.SUCCESS)

    # Create new storage instance
    new_storage = LineageStorage(str(temp_lineage_dir))
    metrics = get_aggregated_metrics(new_storage)

    assert metrics["document_count"] == 1, "Metrics should persist across storage instances"
    assert metrics["processing"]["completed_docs"] == 1, "Processing status should persist"
