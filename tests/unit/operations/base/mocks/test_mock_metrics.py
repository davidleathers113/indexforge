"""Test metrics tracking using mocks.

Tests the behavior of performance and error tracking metrics using mocked components.
"""

from unittest.mock import Mock, patch

import pytest
from weaviate.collections import Collection

from src.api.repositories.weaviate.metrics import (
    BatchMetrics,
    BatchPerformanceTracker,
    MetricsObserver,
)
from src.api.repositories.weaviate.operations.base import BatchOperation


class TestMetricsBatchOperation(BatchOperation):
    """Test implementation of BatchOperation for metrics testing."""

    def __init__(self, collection, batch_size, metrics=None, performance_tracker=None):
        super().__init__(collection, batch_size)
        self.metrics = metrics or BatchMetrics()
        self.performance_tracker = performance_tracker or BatchPerformanceTracker()

    def prepare_item(self, item):
        if item.get("fail_prepare"):
            self.metrics.record_error("preparation_error")
            raise ValueError("Preparation failed")
        return {"prepared": item}

    def validate_item(self, item):
        valid = not item.get("invalid")
        if not valid:
            self.metrics.record_error("validation_error")
        return valid

    def process_batch(self, batch):
        if any(item.get("fail_process") for item in batch):
            self.metrics.record_error("processing_error")
            return [{"id": item["id"], "status": "failed"} for item in batch]
        return [{"id": item["id"], "status": "success"} for item in batch]


class MockMetricsObserver(MetricsObserver):
    """Mock implementation of metrics observer for testing."""

    def __init__(self):
        self.notifications = []

    def notify(self, metric_type, value):
        self.notifications.append((metric_type, value))


@pytest.fixture
def mock_collection():
    """Setup mock collection."""
    return Mock(spec=Collection)


@pytest.fixture
def metrics():
    """Setup batch metrics."""
    return BatchMetrics()


@pytest.fixture
def performance_tracker():
    """Setup performance tracker."""
    return BatchPerformanceTracker(min_batch_size=10, max_batch_size=1000)


@pytest.fixture
def metrics_observer():
    """Setup metrics observer."""
    return MockMetricsObserver()


@pytest.fixture
def batch_operation(mock_collection, metrics, performance_tracker):
    """Setup test batch operation with metrics tracking."""
    return TestMetricsBatchOperation(
        collection=mock_collection,
        batch_size=50,
        metrics=metrics,
        performance_tracker=performance_tracker,
    )


def test_successful_operation_metrics(batch_operation):
    """
    Test metrics tracking for successful operations.

    Given: A batch operation with metrics tracking
    When: A successful batch is processed
    Then: Success metrics are properly recorded
    """
    items = [{"id": str(i)} for i in range(5)]
    batch_operation.execute_batch(items)

    assert batch_operation.metrics.get_success_count() == 5, "Should record successful operations"
    assert batch_operation.metrics.get_error_count() == 0, "Should have no errors"


def test_error_tracking(batch_operation):
    """
    Test tracking of different error types.

    Given: A batch operation encountering various errors
    When: Operations fail in different ways
    Then: Error metrics are properly categorized and recorded
    """
    items = [
        {"id": "1", "fail_prepare": True},
        {"id": "2", "invalid": True},
        {"id": "3", "fail_process": True},
    ]

    try:
        batch_operation.execute_batch(items)
    except ValueError:
        pass

    error_counts = batch_operation.metrics.get_error_counts()
    assert error_counts["preparation_error"] == 1, "Should record preparation error"
    assert error_counts["validation_error"] == 1, "Should record validation error"


def test_performance_metrics(batch_operation):
    """
    Test tracking of performance metrics.

    Given: A batch operation processing items
    When: Multiple batches are processed
    Then: Performance metrics are accurately tracked
    """
    # Process multiple batches
    for _ in range(3):
        items = [{"id": str(i)} for i in range(10)]
        batch_operation.execute_batch(items)

    metrics = batch_operation.performance_tracker.get_metrics()
    assert "throughput" in metrics, "Should track throughput"
    assert "batch_sizes" in metrics, "Should track batch sizes"
    assert len(metrics["batch_sizes"]) == 3, "Should record all batch operations"


def test_metrics_observer_notifications(batch_operation, metrics_observer):
    """
    Test observer notifications for metrics events.

    Given: A batch operation with attached metrics observer
    When: Operations generate metrics
    Then: Observer is properly notified
    """
    batch_operation.metrics.add_observer(metrics_observer)

    items = [{"id": "1", "fail_process": True}]
    batch_operation.execute_batch(items)

    assert len(metrics_observer.notifications) > 0, "Observer should receive notifications"
    assert any(
        n[0] == "error" for n in metrics_observer.notifications
    ), "Should notify about errors"


def test_batch_size_metrics(batch_operation):
    """
    Test tracking of batch size adjustments.

    Given: A batch operation with performance tracking
    When: Batch sizes are adjusted
    Then: Size changes are properly tracked
    """
    initial_size = batch_operation.batch_size

    # Process batches to trigger size adjustments
    for _ in range(3):
        items = [{"id": str(i)} for i in range(20)]
        batch_operation.execute_batch(items)

    size_metrics = batch_operation.performance_tracker.get_metrics()["batch_sizes"]
    assert len(size_metrics) > 0, "Should track batch size changes"
    assert size_metrics[0] == initial_size, "Should record initial size"


def test_error_rate_impact(batch_operation):
    """
    Test error rate calculation and tracking.

    Given: A batch operation experiencing errors
    When: Operations fail at a certain rate
    Then: Error rate metrics are accurately calculated
    """
    # Process batch with 50% failure rate
    items = [
        {"id": "1"},
        {"id": "2", "fail_process": True},
        {"id": "3"},
        {"id": "4", "fail_process": True},
    ]

    batch_operation.execute_batch(items)

    metrics = batch_operation.performance_tracker.get_metrics()
    assert "error_rate" in metrics, "Should track error rate"
    assert metrics["error_rate"] == 0.5, "Should calculate correct error rate"


@patch("time.time")
def test_throughput_calculation(mock_time, batch_operation):
    """
    Test throughput metric calculation.

    Given: A batch operation processing items
    When: Operations are timed
    Then: Throughput is correctly calculated
    """
    mock_time.side_effect = [0, 2]  # 2 second operation

    items = [{"id": str(i)} for i in range(10)]
    batch_operation.execute_batch(items)

    metrics = batch_operation.performance_tracker.get_metrics()
    assert metrics["throughput"] == 5.0, "Should calculate items per second"
