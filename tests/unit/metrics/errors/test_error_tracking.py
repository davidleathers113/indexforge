"""Test error type tracking functionality."""

from concurrent.futures import ThreadPoolExecutor
import threading

import pytest

from src.api.repositories.weaviate.metrics import BatchMetrics


@pytest.fixture
def batch_metrics():
    """Setup BatchMetrics instance."""
    return BatchMetrics()


def test_error_type_initialization(batch_metrics):
    """
    Test error tracking initialization.

    Given: A new BatchMetrics instance
    When: Instance is created
    Then: Error types dictionary is empty
    """
    assert len(batch_metrics.error_types) == 0


def test_single_error_type_recording(batch_metrics):
    """
    Test single error type recording.

    Given: A BatchMetrics instance
    When: record_batch_error is called once
    Then: Error type is recorded with count of 1
    """
    error_type = "validation_error"
    batch_metrics.record_batch_error(error_type)
    assert batch_metrics.error_types[error_type] == 1


def test_multiple_same_error_recording(batch_metrics):
    """
    Test multiple recordings of same error type.

    Given: A BatchMetrics instance
    When: record_batch_error is called multiple times with same error
    Then: Error count is incremented correctly
    """
    error_type = "timeout_error"
    num_errors = 5

    for _ in range(num_errors):
        batch_metrics.record_batch_error(error_type)

    assert batch_metrics.error_types[error_type] == num_errors


def test_multiple_error_types_recording(batch_metrics):
    """
    Test recording of multiple error types.

    Given: A BatchMetrics instance
    When: Different error types are recorded
    Then: Each error type has correct count
    """
    error_types = {"validation_error": 3, "timeout_error": 2, "connection_error": 1}

    for error_type, count in error_types.items():
        for _ in range(count):
            batch_metrics.record_batch_error(error_type)

    for error_type, expected_count in error_types.items():
        assert batch_metrics.error_types[error_type] == expected_count


def test_thread_safe_error_recording(batch_metrics):
    """
    Test thread-safe error recording.

    Given: A BatchMetrics instance
    When: Multiple threads record errors simultaneously
    Then: Error counts are accurate
    """
    error_types = ["timeout", "validation", "network"]
    num_threads = 10

    def record_errors():
        for error_type in error_types:
            batch_metrics.record_batch_error(error_type)

    threads = [threading.Thread(target=record_errors) for _ in range(num_threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    for error_type in error_types:
        assert batch_metrics.error_types[error_type] == num_threads


def test_error_recording_with_reset(batch_metrics):
    """
    Test error recording with reset.

    Given: A BatchMetrics instance with recorded errors
    When: reset_metrics is called
    Then: Error types are cleared
    """
    error_types = ["timeout", "validation"]
    for error_type in error_types:
        batch_metrics.record_batch_error(error_type)

    batch_metrics.reset_metrics()
    assert len(batch_metrics.error_types) == 0


def test_concurrent_error_recording_and_reset(batch_metrics):
    """
    Test concurrent error recording and reset.

    Given: A BatchMetrics instance
    When: Errors are recorded while reset operations occur
    Then: Error tracking remains consistent
    """

    def record_errors():
        for _ in range(50):
            batch_metrics.record_batch_error("test_error")

    def reset_metrics():
        for _ in range(5):
            batch_metrics.reset_metrics()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(record_errors), executor.submit(reset_metrics)]
        for future in futures:
            future.result()

    # Verify the error_types dict is in a valid state
    assert isinstance(batch_metrics.error_types, dict)
    if "test_error" in batch_metrics.error_types:
        assert isinstance(batch_metrics.error_types["test_error"], int)
        assert batch_metrics.error_types["test_error"] >= 0
