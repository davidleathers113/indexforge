"""Test basic operations of BatchPerformanceTracker."""

import pytest

from src.api.repositories.weaviate.metrics import BatchPerformanceTracker


@pytest.fixture
def performance_tracker():
    """Setup BatchPerformanceTracker instance."""
    return BatchPerformanceTracker(min_batch_size=10, max_batch_size=100, window_size=5)


def test_start_batch_initializes_tracking(performance_tracker):
    """
    Test batch tracking initialization.

    Given: A BatchPerformanceTracker instance
    When: start_batch is called
    Then: Tracking is initialized with correct batch size
    """
    batch_size = 50
    performance_tracker.start_batch(batch_size)
    assert performance_tracker.current_batch_size == batch_size


def test_end_batch_updates_performance_metrics(performance_tracker):
    """
    Test performance metrics update.

    Given: A BatchPerformanceTracker with active batch
    When: end_batch is called with results
    Then: Performance metrics are updated correctly
    """
    batch_size = 50
    successful = 45
    failed = 5
    memory_usage = 100.0

    performance_tracker.start_batch(batch_size)
    performance_tracker.end_batch(successful, failed, memory_usage)

    metrics = performance_tracker.get_performance_metrics()
    assert metrics["success_rate"] == successful / batch_size
    assert metrics["error_rate"] == failed / batch_size
    assert metrics["memory_usage_mb"] == memory_usage


def test_end_batch_without_start(performance_tracker):
    """
    Test ending batch without starting.

    Given: A BatchPerformanceTracker instance
    When: end_batch is called without start_batch
    Then: Operation is handled gracefully
    """
    performance_tracker.end_batch(10, 0, 100.0)
    metrics = performance_tracker.get_performance_metrics()
    assert metrics["success_rate"] == 0.0
    assert metrics["error_rate"] == 0.0


def test_reset_performance_metrics_clears_tracking_data(performance_tracker):
    """
    Test performance metrics reset.

    Given: A BatchPerformanceTracker with recorded data
    When: reset_performance_metrics is called
    Then: All tracking data is cleared
    """
    # Record some performance data
    performance_tracker.start_batch(50)
    performance_tracker.end_batch(45, 5, 100.0)

    performance_tracker.reset_performance_metrics()

    metrics = performance_tracker.get_performance_metrics()
    assert metrics["success_rate"] == 0.0
    assert metrics["error_rate"] == 0.0
    assert metrics["memory_usage_mb"] == 0.0
