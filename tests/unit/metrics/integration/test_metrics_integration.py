"""Test integration between different metrics components."""

from time import sleep

import pytest

from src.api.repositories.weaviate.metrics import BatchMetrics


@pytest.fixture
def batch_metrics():
    """Setup BatchMetrics instance."""
    return BatchMetrics()


def test_batch_completion_with_object_tracking(batch_metrics):
    """
    Test batch completion with object tracking.

    Given: A BatchMetrics instance
    When: A batch completes with object successes and failures
    Then: Both batch and object metrics are updated correctly
    """
    # Record object results
    successful = 8
    failed = 2
    for _ in range(successful):
        batch_metrics.record_object_success()
    for _ in range(failed):
        batch_metrics.record_object_error()

    # Complete the batch
    batch_metrics.record_batch_completion()

    summary = batch_metrics.get_metrics_summary()
    assert summary["total_batches"] == 1
    assert summary["successful_objects"] == successful
    assert summary["failed_objects"] == failed


def test_error_tracking_with_batch_timing(batch_metrics):
    """
    Test error tracking with batch timing.

    Given: A BatchMetrics instance
    When: Errors occur during a timed batch
    Then: Both timing and error metrics are recorded correctly
    """
    with batch_metrics.time_batch():
        # Simulate work with errors
        sleep(0.1)
        batch_metrics.record_object_error()
        batch_metrics.record_batch_error("timeout_error")

    metrics = batch_metrics.get_metrics_summary()
    assert metrics["failed_objects"] == 1
    assert metrics["error_types"]["timeout_error"] == 1
    assert batch_metrics.total_batch_time > 0


def test_batch_size_with_success_tracking(batch_metrics):
    """
    Test batch size tracking with success recording.

    Given: A BatchMetrics instance
    When: Processing a batch of specific size with successes
    Then: Both size and success metrics are updated correctly
    """
    batch_size = 10
    batch_metrics.record_batch_size(batch_size)

    # Record successful processing
    for _ in range(batch_size):
        batch_metrics.record_object_success()

    assert batch_metrics.total_objects == batch_size
    assert batch_metrics.successful_objects == batch_size
    assert batch_metrics.average_batch_size == batch_size


def test_complete_batch_workflow(batch_metrics):
    """
    Test complete batch processing workflow.

    Given: A BatchMetrics instance
    When: Running a complete batch workflow
    Then: All metrics components are updated correctly
    """
    batch_size = 20
    successful = 15
    failed = 5

    # Start timing
    with batch_metrics.time_batch():
        # Record batch size
        batch_metrics.record_batch_size(batch_size)

        # Process objects
        for _ in range(successful):
            batch_metrics.record_object_success()
        for _ in range(failed):
            batch_metrics.record_object_error()

        # Record some errors
        batch_metrics.record_batch_error("validation_error")
        batch_metrics.record_batch_error("timeout_error")

        # Small delay to ensure measurable timing
        sleep(0.1)

    # Complete the batch
    batch_metrics.record_batch_completion()

    # Verify all metrics
    summary = batch_metrics.get_metrics_summary()
    assert summary["total_batches"] == 1
    assert summary["successful_objects"] == successful
    assert summary["failed_objects"] == failed
    assert summary["error_types"]["validation_error"] == 1
    assert summary["error_types"]["timeout_error"] == 1
    assert batch_metrics.total_batch_time > 0
    assert batch_metrics.average_batch_size == batch_size


def test_metrics_reset_integration(batch_metrics):
    """
    Test metrics reset across all components.

    Given: A BatchMetrics instance with data in all components
    When: reset_metrics is called
    Then: All components are reset correctly
    """
    # Record data in all components
    with batch_metrics.time_batch():
        batch_metrics.record_batch_size(10)
        batch_metrics.record_object_success()
        batch_metrics.record_object_error()
        batch_metrics.record_batch_error("test_error")
        sleep(0.1)

    batch_metrics.record_batch_completion()

    # Verify data was recorded
    assert batch_metrics.total_batch_time > 0
    assert batch_metrics.total_objects > 0
    assert len(batch_metrics.error_types) > 0
    assert batch_metrics.total_batches > 0

    # Reset metrics
    batch_metrics.reset_metrics()

    # Verify all components are reset
    summary = batch_metrics.get_metrics_summary()
    assert summary["total_batches"] == 0
    assert summary["successful_objects"] == 0
    assert summary["failed_objects"] == 0
    assert len(summary["error_types"]) == 0
    assert batch_metrics.total_batch_time == 0
    assert batch_metrics.average_batch_size == 0


def test_concurrent_integrated_operations(batch_metrics):
    """
    Test concurrent operations across multiple components.

    Given: A BatchMetrics instance
    When: Multiple components are updated concurrently
    Then: All metrics remain consistent
    """
    import threading

    def worker():
        with batch_metrics.time_batch():
            batch_metrics.record_batch_size(5)
            batch_metrics.record_object_success()
            batch_metrics.record_object_error()
            batch_metrics.record_batch_error("worker_error")
            sleep(0.1)
        batch_metrics.record_batch_completion()

    # Run multiple workers
    threads = [threading.Thread(target=worker) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Verify metrics consistency
    summary = batch_metrics.get_metrics_summary()
    assert summary["total_batches"] == 3
    assert summary["successful_objects"] == 3
    assert summary["failed_objects"] == 3
    assert summary["error_types"]["worker_error"] == 3
    assert batch_metrics.total_batch_time > 0
