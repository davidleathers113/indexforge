"""Test concurrent operations in performance tracking."""

import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest

from src.api.repositories.weaviate.metrics import BatchPerformanceTracker


@pytest.fixture
def performance_tracker():
    """Setup BatchPerformanceTracker instance."""
    return BatchPerformanceTracker(min_batch_size=10, max_batch_size=100, window_size=5)


@pytest.mark.asyncio
async def test_concurrent_batch_tracking(performance_tracker):
    """
    Test concurrent batch tracking.

    Given: Multiple concurrent batch operations
    When: Tracking multiple batches simultaneously
    Then: Performance metrics remain consistent
    """

    async def track_batch(batch_size, success_rate):
        performance_tracker.start_batch(batch_size)
        successful = int(batch_size * success_rate)
        failed = batch_size - successful
        performance_tracker.end_batch(successful, failed, 100.0)
        return performance_tracker.get_optimal_batch_size()

    tasks = [
        track_batch(50, 0.9),  # High success rate
        track_batch(50, 0.5),  # Medium success rate
        track_batch(50, 0.1),  # Low success rate
    ]

    results = await asyncio.gather(*tasks)
    assert all(
        performance_tracker.min_batch_size <= size <= performance_tracker.max_batch_size
        for size in results
    )


def test_concurrent_memory_tracking(performance_tracker):
    """
    Test concurrent memory usage tracking.

    Given: Multiple threads tracking memory usage
    When: Recording memory metrics concurrently
    Then: Memory tracking remains accurate
    """

    def track_memory_usage(memory_mb):
        performance_tracker.start_batch(50)
        performance_tracker.end_batch(45, 5, memory_mb)

    memory_values = [100.0, 500.0, 1000.0, 1500.0]

    with ThreadPoolExecutor(max_workers=len(memory_values)) as executor:
        futures = [executor.submit(track_memory_usage, memory_mb) for memory_mb in memory_values]
        for future in futures:
            future.result()

    metrics = performance_tracker.get_performance_metrics()
    assert isinstance(metrics["memory_usage_mb"], float)
    assert metrics["memory_usage_mb"] > 0


@pytest.mark.asyncio
async def test_concurrent_optimization_stability(performance_tracker):
    """
    Test stability of batch size optimization under concurrent load.

    Given: Multiple concurrent optimization requests
    When: Getting optimal batch size concurrently
    Then: Optimization remains stable and consistent
    """

    async def optimize_batch_size():
        performance_tracker.start_batch(50)
        performance_tracker.end_batch(45, 5, 100.0)
        return performance_tracker.get_optimal_batch_size()

    num_concurrent = 10
    tasks = [optimize_batch_size() for _ in range(num_concurrent)]

    results = await asyncio.gather(*tasks)

    # Verify all results are within valid range
    assert all(
        performance_tracker.min_batch_size <= size <= performance_tracker.max_batch_size
        for size in results
    )

    # Verify stability - results should not vary too much
    size_variance = max(results) - min(results)
    assert (
        size_variance
        <= (performance_tracker.max_batch_size - performance_tracker.min_batch_size) / 2
    )


def test_concurrent_mixed_operations(performance_tracker):
    """
    Test concurrent mixed operations.

    Given: Multiple threads performing different operations
    When: Running mixed operations concurrently
    Then: Performance tracking remains consistent
    """

    def success_operation():
        performance_tracker.start_batch(50)
        performance_tracker.end_batch(50, 0, 100.0)

    def failure_operation():
        performance_tracker.start_batch(50)
        performance_tracker.end_batch(0, 50, 1000.0)

    def memory_intensive_operation():
        performance_tracker.start_batch(30)
        performance_tracker.end_batch(25, 5, 2000.0)

    operations = [success_operation, failure_operation, memory_intensive_operation]

    with ThreadPoolExecutor(max_workers=len(operations)) as executor:
        futures = [executor.submit(op) for op in operations]
        for future in futures:
            future.result()

    # Verify tracker state is consistent
    metrics = performance_tracker.get_performance_metrics()
    assert isinstance(metrics["success_rate"], float)
    assert isinstance(metrics["error_rate"], float)
    assert isinstance(metrics["memory_usage_mb"], float)
    assert 0 <= metrics["success_rate"] <= 1
    assert 0 <= metrics["error_rate"] <= 1
    assert metrics["memory_usage_mb"] >= 0
