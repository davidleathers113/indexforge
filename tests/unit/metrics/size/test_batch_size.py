"""Test batch size tracking functionality."""

import pytest

from src.api.repositories.weaviate.metrics import BatchMetrics


@pytest.fixture
def batch_metrics():
    """Setup BatchMetrics instance."""
    return BatchMetrics()


def test_batch_size_initialization(batch_metrics):
    """
    Test size tracking initialization.

    Given: A new BatchMetrics instance
    When: Instance is created
    Then: Size metrics start at zero
    """
    assert batch_metrics.total_objects == 0
    assert batch_metrics.average_batch_size == 0
    assert batch_metrics.min_batch_size == float("inf")
    assert batch_metrics.max_batch_size == 0


def test_record_batch_size_single(batch_metrics):
    """
    Test recording single batch size.

    Given: A BatchMetrics instance
    When: A single batch size is recorded
    Then: All size metrics reflect that single batch
    """
    batch_size = 10
    batch_metrics.record_batch_size(batch_size)

    assert batch_metrics.total_objects == batch_size
    assert batch_metrics.average_batch_size == batch_size
    assert batch_metrics.min_batch_size == batch_size
    assert batch_metrics.max_batch_size == batch_size


def test_record_batch_size_multiple(batch_metrics):
    """
    Test recording multiple batch sizes.

    Given: A BatchMetrics instance
    When: Multiple different batch sizes are recorded
    Then: Size metrics reflect all batches correctly
    """
    batch_sizes = [5, 10, 3]
    total_objects = sum(batch_sizes)
    num_batches = len(batch_sizes)

    for size in batch_sizes:
        batch_metrics.record_batch_size(size)

    assert batch_metrics.total_objects == total_objects
    assert batch_metrics.average_batch_size == total_objects / num_batches
    assert batch_metrics.min_batch_size == min(batch_sizes)
    assert batch_metrics.max_batch_size == max(batch_sizes)


def test_record_batch_size_zero(batch_metrics):
    """
    Test recording zero batch size.

    Given: A BatchMetrics instance
    When: A zero batch size is recorded
    Then: Metrics are updated appropriately
    """
    batch_metrics.record_batch_size(0)

    assert batch_metrics.total_objects == 0
    assert batch_metrics.average_batch_size == 0
    assert batch_metrics.min_batch_size == 0
    assert batch_metrics.max_batch_size == 0


def test_record_batch_size_mixed_values(batch_metrics):
    """
    Test recording mixed batch sizes including zero.

    Given: A BatchMetrics instance
    When: Mixed batch sizes including zero are recorded
    Then: Metrics correctly reflect all values
    """
    batch_sizes = [0, 5, 10, 0, 3]
    total_objects = sum(batch_sizes)
    num_batches = len(batch_sizes)

    for size in batch_sizes:
        batch_metrics.record_batch_size(size)

    assert batch_metrics.total_objects == total_objects
    assert batch_metrics.average_batch_size == total_objects / num_batches
    assert batch_metrics.min_batch_size == min(batch_sizes)
    assert batch_metrics.max_batch_size == max(batch_sizes)
