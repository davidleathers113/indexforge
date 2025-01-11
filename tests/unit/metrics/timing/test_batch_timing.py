"""Test batch timing functionality."""

from time import sleep

import pytest

from src.api.repositories.weaviate.metrics import BatchMetrics


@pytest.fixture
def batch_metrics():
    """Setup BatchMetrics instance."""
    return BatchMetrics()


def test_batch_timing_initialization(batch_metrics):
    """
    Test timing initialization.

    Given: A new BatchMetrics instance
    When: Instance is created
    Then: Total time and average time are zero
    """
    assert batch_metrics.total_batch_time == 0
    assert batch_metrics.average_batch_time == 0


def test_batch_timing_single_batch(batch_metrics):
    """
    Test timing for a single batch.

    Given: A BatchMetrics instance
    When: A single batch is timed
    Then: Total time equals batch time and average equals total
    """
    sleep_duration = 0.1
    with batch_metrics.time_batch():
        sleep(sleep_duration)

    assert batch_metrics.total_batch_time > 0
    assert batch_metrics.total_batch_time >= sleep_duration
    assert batch_metrics.average_batch_time == batch_metrics.total_batch_time


def test_batch_timing_multiple_batches(batch_metrics):
    """
    Test timing for multiple batches.

    Given: A BatchMetrics instance
    When: Multiple batches are timed
    Then: Total and average times are calculated correctly
    """
    sleep_duration = 0.1
    num_batches = 3

    for _ in range(num_batches):
        with batch_metrics.time_batch():
            sleep(sleep_duration)

    assert batch_metrics.total_batch_time >= sleep_duration * num_batches
    assert batch_metrics.average_batch_time == batch_metrics.total_batch_time / num_batches


def test_batch_timing_context_manager(batch_metrics):
    """
    Test timing context manager behavior.

    Given: A BatchMetrics instance
    When: Context manager is used
    Then: Timing is automatically handled
    """
    with batch_metrics.time_batch() as timer:
        assert timer.start_time > 0
        sleep(0.1)

    assert timer.end_time > timer.start_time
    assert batch_metrics.total_batch_time > 0
