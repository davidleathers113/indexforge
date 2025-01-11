"""Test batch completion counter functionality."""

import pytest

from src.api.repositories.weaviate.metrics import BatchMetrics


@pytest.fixture
def batch_metrics():
    """Setup BatchMetrics instance."""
    return BatchMetrics()


def test_batch_completion_counter_initialization(batch_metrics):
    """
    Test counter initialization.

    Given: A new BatchMetrics instance
    When: Instance is created
    Then: Batch counter starts at zero
    """
    assert batch_metrics.total_batches == 0


def test_batch_completion_counter_increment(batch_metrics):
    """
    Test counter increment.

    Given: A BatchMetrics instance
    When: record_batch_completion is called
    Then: Counter is incremented by one
    """
    initial_count = batch_metrics.total_batches
    batch_metrics.record_batch_completion()
    assert batch_metrics.total_batches == initial_count + 1


def test_batch_completion_counter_multiple_increments(batch_metrics):
    """
    Test multiple counter increments.

    Given: A BatchMetrics instance
    When: record_batch_completion is called multiple times
    Then: Counter reflects total number of calls
    """
    num_completions = 5
    for _ in range(num_completions):
        batch_metrics.record_batch_completion()
    assert batch_metrics.total_batches == num_completions
