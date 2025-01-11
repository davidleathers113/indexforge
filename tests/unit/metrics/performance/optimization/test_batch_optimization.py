"""Test batch size optimization functionality."""

import sys

import pytest

from src.api.repositories.weaviate.metrics import BatchPerformanceTracker


@pytest.fixture
def performance_tracker():
    """Setup BatchPerformanceTracker instance."""
    return BatchPerformanceTracker(min_batch_size=10, max_batch_size=100, window_size=5)


def test_get_optimal_batch_size_increases_on_success(performance_tracker):
    """
    Test batch size optimization for successful batches.

    Given: A BatchPerformanceTracker with successful batches
    When: get_optimal_batch_size is called
    Then: Batch size is increased within limits
    """
    initial_size = 50

    # Process several successful batches
    for _ in range(3):
        performance_tracker.start_batch(initial_size)
        performance_tracker.end_batch(
            successful_objects=48, failed_objects=2, memory_usage_mb=100.0
        )

    optimal_size = performance_tracker.get_optimal_batch_size()
    assert optimal_size > initial_size
    assert optimal_size <= performance_tracker.max_batch_size


def test_get_optimal_batch_size_decreases_on_high_error_rate(performance_tracker):
    """
    Test batch size optimization for high error rates.

    Given: A BatchPerformanceTracker with high error rates
    When: get_optimal_batch_size is called
    Then: Batch size is decreased within limits
    """
    initial_size = 50

    # Process several batches with high error rates
    for _ in range(3):
        performance_tracker.start_batch(initial_size)
        performance_tracker.end_batch(
            successful_objects=20, failed_objects=30, memory_usage_mb=100.0
        )

    optimal_size = performance_tracker.get_optimal_batch_size()
    assert optimal_size < initial_size
    assert optimal_size >= performance_tracker.min_batch_size


def test_get_optimal_batch_size_considers_memory_usage(performance_tracker):
    """
    Test batch size optimization with memory constraints.

    Given: A BatchPerformanceTracker with high memory usage
    When: get_optimal_batch_size is called
    Then: Batch size is adjusted based on memory usage
    """
    initial_size = 50
    high_memory_usage = 1000.0  # MB

    performance_tracker.start_batch(initial_size)
    performance_tracker.end_batch(
        successful_objects=45, failed_objects=5, memory_usage_mb=high_memory_usage
    )

    optimal_size = performance_tracker.get_optimal_batch_size()
    assert optimal_size <= initial_size  # Should not increase due to high memory usage


def test_batch_size_at_system_limits(performance_tracker):
    """
    Test batch size handling at system limits.

    Given: A BatchPerformanceTracker with extreme batch sizes
    When: Processing batches at system limits
    Then: Batch sizes are constrained appropriately
    """
    # Test with maximum possible batch size
    max_possible_size = sys.maxsize
    performance_tracker.start_batch(max_possible_size)
    performance_tracker.end_batch(
        successful_objects=max_possible_size - 1, failed_objects=1, memory_usage_mb=100.0
    )

    optimal_size = performance_tracker.get_optimal_batch_size()
    assert optimal_size <= performance_tracker.max_batch_size

    # Test with minimum possible batch size
    performance_tracker.start_batch(1)
    performance_tracker.end_batch(successful_objects=0, failed_objects=1, memory_usage_mb=100.0)

    optimal_size = performance_tracker.get_optimal_batch_size()
    assert optimal_size >= performance_tracker.min_batch_size


def test_rapid_batch_size_fluctuations(performance_tracker):
    """
    Test handling of rapid batch size changes.

    Given: A BatchPerformanceTracker with rapidly changing conditions
    When: Processing batches with alternating success/failure patterns
    Then: Batch size adjustments remain stable
    """
    initial_size = 50

    # Alternate between success and failure
    for i in range(10):
        performance_tracker.start_batch(initial_size)
        if i % 2 == 0:
            # Success case
            performance_tracker.end_batch(
                successful_objects=initial_size, failed_objects=0, memory_usage_mb=100.0
            )
        else:
            # Failure case
            performance_tracker.end_batch(
                successful_objects=0, failed_objects=initial_size, memory_usage_mb=1000.0
            )

    optimal_size = performance_tracker.get_optimal_batch_size()
    assert performance_tracker.min_batch_size <= optimal_size <= performance_tracker.max_batch_size
