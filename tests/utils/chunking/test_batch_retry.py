"""Tests for batch retry utilities.

These tests verify the functionality of batch retries, including retry strategies,
error handling, and metrics collection.
"""
import logging
import time
from unittest.mock import MagicMock

import pytest

from src.utils.chunking.batch_retry import BatchItem, BatchRetryManager, RetryConfig, RetryStrategy
from src.utils.chunking.progress_tracking import OperationType, ProgressTracker


@pytest.fixture
def retry_config():
    """Create a retry configuration for testing."""
    return RetryConfig(max_retries=3, initial_delay=0.1, max_delay=1.0, strategy=RetryStrategy.EXPONENTIAL, jitter=0.1)


@pytest.fixture
def retry_manager(retry_config):
    """Create a retry manager for testing."""
    return BatchRetryManager(operation_type=OperationType.BATCH_IMPORT, config=retry_config)


def test_fibonacci_calculation(retry_manager):
    """Test optimized Fibonacci calculation."""
    assert retry_manager._fibonacci(0) == 0
    assert retry_manager._fibonacci(1) == 1
    assert retry_manager._fibonacci(5) == 5
    assert retry_manager._fibonacci(7) == 13
    assert 5 in retry_manager._fib_cache
    assert retry_manager._fib_cache[5] == 5
    assert retry_manager._fibonacci(10) == 55
    assert retry_manager._fibonacci(10) == 55


def test_retry_delay_calculation(retry_manager):
    """Test retry delay calculation for different strategies."""
    retry_manager.config.strategy = RetryStrategy.EXPONENTIAL
    delays = [retry_manager.calculate_next_delay(i) for i in range(3)]
    assert all(delays[i] < delays[i + 1] for i in range(len(delays) - 1))
    assert all(d <= retry_manager.config.max_delay for d in delays)
    retry_manager.config.strategy = RetryStrategy.LINEAR
    delays = [retry_manager.calculate_next_delay(i) for i in range(3)]
    assert all(d == retry_manager.config.initial_delay for d in delays)
    retry_manager.config.strategy = RetryStrategy.FIBONACCI
    delays = [retry_manager.calculate_next_delay(i) for i in range(3)]
    assert all(delays[i] <= delays[i + 1] for i in range(len(delays) - 1))


def test_should_retry_conditions(retry_manager):
    """Test conditions for retry decisions."""
    current_time = time.time()
    item = BatchItem(data='test', attempt=retry_manager.config.max_retries)
    assert not retry_manager.should_retry(item, current_time)
    item = BatchItem(data='test', next_retry_time=current_time + 1)
    assert not retry_manager.should_retry(item, current_time)
    assert retry_manager.should_retry(item, current_time + 2)
    retry_manager.config.timeout = 1.0
    retry_manager._start_time = current_time - 2.0
    assert not retry_manager.should_retry(item, current_time)


def test_successful_batch_processing(retry_manager):
    """Test processing a batch with no failures."""
    items = list(range(5))
    results = retry_manager.process_batch(items, lambda x: x * 2)
    assert len(results) == 5
    assert results == [i * 2 for i in items]
    assert retry_manager.metrics.total_retries == 0
    assert retry_manager.metrics.successful_retries == 0
    assert retry_manager.metrics.failed_retries == 0


def test_retry_with_eventual_success(retry_manager):
    """Test retrying failed operations with eventual success."""
    attempts = {}

    def flaky_operation(x):
        attempts[x] = attempts.get(x, 0) + 1
        if attempts[x] < 2:
            raise ValueError(f'Attempt {attempts[x]} failed')
        return x * 2
    items = list(range(3))
    results = retry_manager.process_batch(items, flaky_operation)
    assert len(results) == 3
    assert results == [i * 2 for i in items]
    assert retry_manager.metrics.total_retries == 3
    assert retry_manager.metrics.successful_retries == 3
    assert retry_manager.metrics.failed_retries == 0
    assert 'ValueError' in retry_manager.metrics.error_types


def test_max_retries_exceeded(retry_manager):
    """Test handling when max retries is exceeded."""

    def failing_operation(x):
        raise ValueError('Always fails')
    items = list(range(2))
    results = retry_manager.process_batch(items, failing_operation)
    assert len(results) == 0
    assert retry_manager.metrics.total_retries == 6
    assert retry_manager.metrics.successful_retries == 0
    assert retry_manager.metrics.failed_retries == 6


def test_selective_retry(retry_manager):
    """Test selective retry based on error type."""

    def should_retry_error(e):
        return isinstance(e, ValueError)

    def selective_operation(x):
        if x == 0:
            raise ValueError('Retryable error')
        elif x == 1:
            raise TypeError('Non-retryable error')
        return x * 2
    items = list(range(3))
    results = retry_manager.process_batch(items, selective_operation, should_retry_error)
    assert len(results) == 1
    assert results == [4]
    assert 'ValueError' in retry_manager.metrics.error_types
    assert 'TypeError' in retry_manager.metrics.error_types


def test_progress_tracking_integration():
    """Test integration with progress tracking."""
    progress_tracker = ProgressTracker(operation_type=OperationType.BATCH_IMPORT, total_items=3, batch_size=1)
    retry_manager = BatchRetryManager(operation_type=OperationType.BATCH_IMPORT, config=RetryConfig(max_retries=2), progress_tracker=progress_tracker)

    def flaky_operation(x):
        if x == 1 and (not hasattr(flaky_operation, 'attempts')):
            flaky_operation.attempts = 1
            raise ValueError('First attempt fails')
        return x
    items = [0, 1, 2]
    retry_manager.process_batch(items, flaky_operation)
    assert progress_tracker.progress.items_completed == 3
    assert progress_tracker.progress.items_failed == 0


def test_metrics_summary(retry_manager):
    """Test metrics summary generation."""

    def flaky_operation(x):
        if x % 2 == 0:
            raise ValueError(f'Error for {x}')
        return x
    items = list(range(4))
    retry_manager.process_batch(items, flaky_operation)
    summary = retry_manager.get_metrics_summary()
    assert 'total_retries' in summary
    assert 'success_rate' in summary
    assert 'error_types' in summary
    assert isinstance(summary['avg_retry_delay'], float)


def test_timeout_handling(retry_manager):
    """Test handling of overall timeout."""
    retry_manager.config.timeout = 0.5

    def slow_operation(x):
        time.sleep(0.2)
        if x % 2 == 0:
            raise ValueError(f'Error for {x}')
        return x
    items = list(range(4))
    results = retry_manager.process_batch(items, slow_operation)
    assert len(results) < 4
    assert retry_manager.metrics.total_retry_time >= 0.5


def test_failure_callback(retry_manager):
    """Test failure callback functionality."""
    failure_mock = MagicMock()
    retry_manager.config.failure_callback = failure_mock

    def failing_operation(x):
        if x % 2 == 0:
            raise ValueError(f'Error for {x}')
        elif x % 3 == 0:
            raise TypeError(f'Type error for {x}')
        return x
    items = list(range(6))
    retry_manager.process_batch(items, failing_operation)
    assert failure_mock.call_count > 0
    for call in failure_mock.call_args_list:
        args = call[0]
        assert isinstance(args[0], int)
        assert isinstance(args[1], Exception)


def test_logging_output(retry_manager, caplog):
    """Test logging output during retry operations."""
    caplog.set_level(logging.DEBUG)

    def flaky_operation(x):
        if x == 1:
            raise ValueError('Test error')
        return x
    items = [0, 1, 2]
    retry_manager.process_batch(items, flaky_operation)
    assert any('Starting batch processing' in record.message for record in caplog.records)
    assert any('Retrying item' in record.message for record in caplog.records)
    assert any('Operation failed' in record.message for record in caplog.records)
    assert any('Batch processing completed' in record.message for record in caplog.records)


def test_delay_calculation_logging(retry_manager, caplog):
    """Test logging of delay calculations."""
    caplog.set_level(logging.DEBUG)
    for strategy in RetryStrategy:
        retry_manager.config.strategy = strategy
        retry_manager.calculate_next_delay(1)
    assert any('linear delay' in record.message.lower() for record in caplog.records)
    assert any('exponential delay' in record.message.lower() for record in caplog.records)
    assert any('fibonacci delay' in record.message.lower() for record in caplog.records)
    assert any('applied jitter' in record.message.lower() for record in caplog.records)