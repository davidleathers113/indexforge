"""Test metrics summary functionality."""

import pytest

from src.api.repositories.weaviate.metrics import BatchMetrics


@pytest.fixture
def batch_metrics():
    """Setup BatchMetrics instance."""
    return BatchMetrics()


def test_empty_metrics_summary(batch_metrics):
    """
    Test metrics summary for new instance.

    Given: A new BatchMetrics instance
    When: get_metrics_summary is called
    Then: Summary contains zero values
    """
    summary = batch_metrics.get_metrics_summary()

    assert summary["total_batches"] == 0
    assert summary["successful_objects"] == 0
    assert summary["failed_objects"] == 0
    assert isinstance(summary["error_types"], dict)
    assert len(summary["error_types"]) == 0


def test_complete_metrics_summary(batch_metrics):
    """
    Test metrics summary with all types of data.

    Given: A BatchMetrics instance with various recorded data
    When: get_metrics_summary is called
    Then: Summary reflects all recorded metrics
    """
    # Record batch completions
    num_batches = 3
    for _ in range(num_batches):
        batch_metrics.record_batch_completion()

    # Record object successes and failures
    num_successes = 50
    num_failures = 10
    for _ in range(num_successes):
        batch_metrics.record_object_success()
    for _ in range(num_failures):
        batch_metrics.record_object_error()

    # Record error types
    error_types = {"validation_error": 2, "timeout_error": 3}
    for error_type, count in error_types.items():
        for _ in range(count):
            batch_metrics.record_batch_error(error_type)

    summary = batch_metrics.get_metrics_summary()

    assert summary["total_batches"] == num_batches
    assert summary["successful_objects"] == num_successes
    assert summary["failed_objects"] == num_failures
    for error_type, count in error_types.items():
        assert summary["error_types"][error_type] == count


def test_metrics_summary_after_reset(batch_metrics):
    """
    Test metrics summary after reset.

    Given: A BatchMetrics instance with data that is reset
    When: get_metrics_summary is called after reset
    Then: Summary shows zero/empty values
    """
    # Record some data
    batch_metrics.record_batch_completion()
    batch_metrics.record_object_success()
    batch_metrics.record_batch_error("test_error")

    # Reset metrics
    batch_metrics.reset_metrics()

    summary = batch_metrics.get_metrics_summary()
    assert summary["total_batches"] == 0
    assert summary["successful_objects"] == 0
    assert summary["failed_objects"] == 0
    assert len(summary["error_types"]) == 0


def test_metrics_summary_with_high_counts(batch_metrics):
    """
    Test metrics summary with high count values.

    Given: A BatchMetrics instance with large numbers of records
    When: get_metrics_summary is called
    Then: Summary handles large numbers correctly
    """
    large_count = 1000000

    # Record large number of completions and objects
    for _ in range(10):  # Reduced for performance
        batch_metrics.record_batch_completion()
    for _ in range(large_count):
        batch_metrics.record_object_success()
    for _ in range(large_count):
        batch_metrics.record_object_error()
    for _ in range(1000):  # Reduced for performance
        batch_metrics.record_batch_error("high_volume_error")

    summary = batch_metrics.get_metrics_summary()

    assert summary["total_batches"] == 10
    assert summary["successful_objects"] == large_count
    assert summary["failed_objects"] == large_count
    assert summary["error_types"]["high_volume_error"] == 1000


def test_metrics_summary_consistency(batch_metrics):
    """
    Test consistency of metrics summary.

    Given: A BatchMetrics instance with repeated summary calls
    When: get_metrics_summary is called multiple times
    Then: Summaries are consistent
    """
    # Record some data
    batch_metrics.record_batch_completion()
    batch_metrics.record_object_success()
    batch_metrics.record_batch_error("test_error")

    # Get multiple summaries
    summary1 = batch_metrics.get_metrics_summary()
    summary2 = batch_metrics.get_metrics_summary()

    # Verify summaries are identical
    assert summary1 == summary2

    # Record more data
    batch_metrics.record_batch_completion()
    batch_metrics.record_object_error()

    # Get new summary
    summary3 = batch_metrics.get_metrics_summary()

    # Verify summary reflects new data
    assert summary3["total_batches"] == summary2["total_batches"] + 1
    assert summary3["failed_objects"] == summary2["failed_objects"] + 1
