"""Tests for progress tracking utilities.

These tests verify the functionality of progress tracking, including batch metrics,
ETA calculation, and the decorator.
"""
from dataclasses import dataclass
import time

import pytest

from src.utils.chunking.progress_tracking import (
    OperationType,
    ProgressTracker,
    track_batch_operation,
)


@pytest.fixture
def progress_tracker():
    """Create a progress tracker for testing."""
    return ProgressTracker(operation_type=OperationType.CHUNKING, total_items=100, batch_size=10, update_interval=0.1)


def test_basic_progress_tracking(progress_tracker):
    """Test basic progress tracking functionality."""
    progress_tracker.start_batch()
    progress_tracker.complete_batch(items_completed=5)
    assert progress_tracker.progress.items_completed == 5
    assert progress_tracker.progress.items_failed == 0
    assert progress_tracker.batch_metrics.batches_completed == 1


def test_batch_metrics(progress_tracker):
    """Test batch metrics calculation."""
    for _ in range(3):
        progress_tracker.start_batch()
        time.sleep(0.1)
        progress_tracker.complete_batch(items_completed=10)
    assert progress_tracker.batch_metrics.batches_completed == 3
    assert progress_tracker.batch_metrics.avg_batch_duration_ms > 0
    assert progress_tracker.batch_metrics.min_batch_duration_ms <= progress_tracker.batch_metrics.max_batch_duration_ms


def test_progress_rate_and_eta(progress_tracker):
    """Test processing rate and ETA calculation."""
    progress_tracker.start_batch()
    time.sleep(0.2)
    progress_tracker.complete_batch(items_completed=20)
    assert progress_tracker.progress.processing_rate > 0
    assert progress_tracker.progress.estimated_remaining_seconds > 0


def test_failed_items_tracking(progress_tracker):
    """Test tracking of failed items."""
    progress_tracker.start_batch()
    progress_tracker.complete_batch(items_completed=8, items_failed=2)
    assert progress_tracker.progress.items_completed == 8
    assert progress_tracker.progress.items_failed == 2


def test_progress_summary(progress_tracker):
    """Test progress summary generation."""
    progress_tracker.start_batch()
    progress_tracker.complete_batch(items_completed=30)
    summary = progress_tracker.get_progress_summary()
    assert summary['operation_type'] == 'CHUNKING'
    assert summary['percent_complete'] == 30.0
    assert summary['items_completed'] == 30
    assert summary['items_total'] == 100
    assert 'batch_metrics' in summary


def test_duration_formatting(progress_tracker):
    """Test duration string formatting."""
    assert progress_tracker._format_duration(0) == 'unknown'
    assert progress_tracker._format_duration(30) == '30s'
    assert progress_tracker._format_duration(90) == '1m 30s'
    assert progress_tracker._format_duration(3700) == '1h 1m 40s'


def test_invalid_batch_completion():
    """Test error handling for invalid batch completion."""
    tracker = ProgressTracker(OperationType.CHUNKING, total_items=10)
    with pytest.raises(ValueError, match='Batch not started'):
        tracker.complete_batch(items_completed=5)


@dataclass
class BatchResult:
    """Test class for batch operation results."""
    completed: int
    failed: int | None = 0


def test_batch_operation_decorator(progress_tracker):
    """Test the batch operation decorator."""

    @track_batch_operation(progress_tracker)
    def successful_batch() -> BatchResult:
        return BatchResult(completed=5, failed=1)

    @track_batch_operation(progress_tracker)
    def failing_batch():
        raise ValueError('Test error')
    successful_batch()
    assert progress_tracker.progress.items_completed == 5
    assert progress_tracker.progress.items_failed == 1
    with pytest.raises(ValueError):
        failing_batch()
    assert progress_tracker.progress.items_failed == 2


def test_zero_total_items():
    """Test handling of zero total items."""
    tracker = ProgressTracker(OperationType.CHUNKING, total_items=0)
    tracker.start_batch()
    tracker.complete_batch(items_completed=0)
    summary = tracker.get_progress_summary()
    assert summary['percent_complete'] == 0
    assert summary['processing_rate'] == 0.0


def test_update_interval(progress_tracker):
    """Test update interval behavior."""
    progress_tracker.start_batch()
    progress_tracker.complete_batch(items_completed=10)
    initial_update_time = progress_tracker.progress.last_update_time
    progress_tracker.start_batch()
    progress_tracker.complete_batch(items_completed=10)
    assert progress_tracker.progress.last_update_time == initial_update_time
    time.sleep(0.2)
    progress_tracker.start_batch()
    progress_tracker.complete_batch(items_completed=10)
    assert progress_tracker.progress.last_update_time > initial_update_time