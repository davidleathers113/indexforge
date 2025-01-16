"""Tests for error tracking utilities.

These tests verify the functionality of error tracking, including error recording,
statistics calculation, and trend analysis.
"""
import time

import pytest

from src.utils.chunking.error_tracking import ErrorCategory, ErrorTracker, track_errors


@pytest.fixture
def error_tracker():
    """Create an error tracker for testing."""
    return ErrorTracker(max_recent_errors=10, error_window_seconds=60)


def test_record_error(error_tracker):
    """Test recording individual errors."""
    error_tracker.record_error(ErrorCategory.REFERENCE_VALIDATION, 'ValidationError', 'Invalid reference format', {'ref_id': '123'})
    stats = error_tracker.get_error_stats()
    assert stats.total_errors == 1
    assert stats.error_counts[ErrorCategory.REFERENCE_VALIDATION] == 1
    assert len(stats.recent_errors) == 1
    assert stats.recent_errors[0].error_type == 'ValidationError'


def test_error_window(error_tracker):
    """Test error statistics respect time window."""
    error_tracker.error_events.append(error_tracker.ErrorEvent(category=ErrorCategory.CACHE_OPERATION, error_type='CacheError', message='Old error', timestamp=time.time() - 120))
    error_tracker.record_error(ErrorCategory.CACHE_OPERATION, 'CacheError', 'Recent error')
    stats = error_tracker.get_error_stats(window_seconds=60)
    assert stats.total_errors == 1


def test_error_rates(error_tracker):
    """Test error rate calculation."""
    for _ in range(10):
        error_tracker.record_operation(ErrorCategory.CLASSIFICATION)
    error_tracker.record_error(ErrorCategory.CLASSIFICATION, 'ClassificationError', 'Error 1')
    error_tracker.record_error(ErrorCategory.CLASSIFICATION, 'ClassificationError', 'Error 2')
    stats = error_tracker.get_error_stats()
    assert stats.error_rates[ErrorCategory.CLASSIFICATION] == 20.0


def test_error_trends(error_tracker):
    """Test error trend analysis."""
    current_time = time.time()
    for i in range(3):
        error_tracker.error_events.append(error_tracker.ErrorEvent(category=ErrorCategory.METADATA_VALIDATION, error_type='ValidationError', message=f'Error {i}', timestamp=current_time - i * 300))
    trends = error_tracker.get_error_trends(num_periods=3, period_seconds=300)
    assert sum(trends[ErrorCategory.METADATA_VALIDATION]) == 3
    assert trends[ErrorCategory.METADATA_VALIDATION] == [1, 1, 1]


def test_frequent_errors(error_tracker):
    """Test frequent error analysis."""
    for _ in range(3):
        error_tracker.record_error(ErrorCategory.REFERENCE_VALIDATION, 'ValidationError', 'Common error')
    error_tracker.record_error(ErrorCategory.CACHE_OPERATION, 'CacheError', 'Rare error')
    frequent = error_tracker.get_frequent_errors(limit=2)
    assert len(frequent) == 2
    assert frequent[0][0] == (ErrorCategory.REFERENCE_VALIDATION, 'ValidationError')
    assert frequent[0][1] == 3


def test_error_summary(error_tracker):
    """Test error summary generation."""
    error_tracker.record_error(ErrorCategory.REFERENCE_VALIDATION, 'ValidationError', 'Test error 1')
    error_tracker.record_error(ErrorCategory.CACHE_OPERATION, 'CacheError', 'Test error 2')
    summary = error_tracker.get_error_summary()
    assert 'Error Summary:' in summary
    assert 'Total Errors: 2' in summary
    assert 'REFERENCE_VALIDATION' in summary
    assert 'CACHE_OPERATION' in summary


def test_max_recent_errors(error_tracker):
    """Test maximum recent errors limit."""
    for i in range(15):
        error_tracker.record_error(ErrorCategory.BATCH_OPERATION, 'BatchError', f'Error {i}')
    assert len(error_tracker.error_events) == 10
    assert error_tracker.error_events[-1].message == 'Error 14'


def test_error_tracking_decorator(error_tracker):
    """Test error tracking decorator."""

    @track_errors(error_tracker, ErrorCategory.CLASSIFICATION)
    def failing_operation():
        raise ValueError('Test error')

    @track_errors(error_tracker, ErrorCategory.CLASSIFICATION)
    def successful_operation():
        return True
    successful_operation()
    assert error_tracker.operation_counts[ErrorCategory.CLASSIFICATION] == 1
    assert error_tracker.get_error_stats().total_errors == 0
    with pytest.raises(ValueError):
        failing_operation()
    stats = error_tracker.get_error_stats()
    assert error_tracker.operation_counts[ErrorCategory.CLASSIFICATION] == 2
    assert stats.total_errors == 1
    assert stats.error_counts[ErrorCategory.CLASSIFICATION] == 1


def test_clear_error_tracker(error_tracker):
    """Test clearing error tracking data."""
    error_tracker.record_error(ErrorCategory.REFERENCE_VALIDATION, 'ValidationError', 'Test error')
    error_tracker.record_operation(ErrorCategory.REFERENCE_VALIDATION)
    error_tracker.clear()
    assert len(error_tracker.error_events) == 0
    assert len(error_tracker.operation_counts) == 0
    assert error_tracker.get_error_stats().total_errors == 0