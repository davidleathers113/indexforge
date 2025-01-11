"""Test object success and failure counter functionality."""

import pytest

from src.api.repositories.weaviate.metrics import BatchMetrics


@pytest.fixture
def batch_metrics():
    """Setup BatchMetrics instance."""
    return BatchMetrics()


def test_object_counters_initialization(batch_metrics):
    """
    Test counter initialization.

    Given: A new BatchMetrics instance
    When: Instance is created
    Then: Success and failure counters start at zero
    """
    assert batch_metrics.successful_objects == 0
    assert batch_metrics.failed_objects == 0


def test_success_counter_increment(batch_metrics):
    """
    Test success counter increment.

    Given: A BatchMetrics instance
    When: record_object_success is called
    Then: Success counter is incremented
    """
    initial_success = batch_metrics.successful_objects
    batch_metrics.record_object_success()
    assert batch_metrics.successful_objects == initial_success + 1
    assert batch_metrics.failed_objects == 0  # Failure counter unchanged


def test_failure_counter_increment(batch_metrics):
    """
    Test failure counter increment.

    Given: A BatchMetrics instance
    When: record_object_error is called
    Then: Failure counter is incremented
    """
    initial_failures = batch_metrics.failed_objects
    batch_metrics.record_object_error()
    assert batch_metrics.failed_objects == initial_failures + 1
    assert batch_metrics.successful_objects == 0  # Success counter unchanged


def test_mixed_counter_increments(batch_metrics):
    """
    Test mixed success and failure recording.

    Given: A BatchMetrics instance
    When: Both successes and failures are recorded
    Then: Both counters reflect correct totals
    """
    successes = 3
    failures = 2

    for _ in range(successes):
        batch_metrics.record_object_success()
    for _ in range(failures):
        batch_metrics.record_object_error()

    assert batch_metrics.successful_objects == successes
    assert batch_metrics.failed_objects == failures
