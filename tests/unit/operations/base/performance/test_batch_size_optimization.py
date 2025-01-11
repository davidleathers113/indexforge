"""Test batch size optimization performance.

Tests the dynamic batch size adjustment mechanisms and their impact on performance.
"""

import time
from unittest.mock import Mock, patch

import pytest
from weaviate.collections import Collection

from src.api.repositories.weaviate.metrics import BatchPerformanceTracker
from src.api.repositories.weaviate.operations.base import BatchOperation


class TestPerformanceBatchOperation(BatchOperation):
    """Test implementation of BatchOperation for performance testing."""

    def __init__(self, collection, batch_size, performance_tracker=None):
        super().__init__(collection, batch_size)
        self.performance_tracker = performance_tracker or BatchPerformanceTracker()
        self.processing_time = 0.01  # Simulated processing time per item

    def prepare_item(self, item):
        return {"prepared": item}

    def validate_item(self, item):
        return True

    def process_batch(self, batch):
        # Simulate processing time based on batch size
        time.sleep(len(batch) * self.processing_time)
        return [{"id": item.get("id", "unknown"), "status": "success"} for item in batch]


@pytest.fixture
def mock_collection():
    """Setup mock collection."""
    return Mock(spec=Collection)


@pytest.fixture
def performance_tracker():
    """Setup performance tracker with test configuration."""
    return BatchPerformanceTracker(min_batch_size=10, max_batch_size=1000, window_size=5)


@pytest.fixture
def batch_operation(mock_collection, performance_tracker):
    """Setup test batch operation with performance tracking."""
    return TestPerformanceBatchOperation(
        collection=mock_collection, batch_size=50, performance_tracker=performance_tracker
    )


def test_initial_batch_size_selection(batch_operation):
    """
    Test initial batch size selection based on system capacity.

    Given: A new batch operation instance with default configuration
    When: The first batch is processed
    Then: The initial batch size should be within defined constraints
    """
    assert 10 <= batch_operation.batch_size <= 1000, "Initial batch size should be within bounds"
    assert batch_operation.batch_size == 50, "Initial batch size should match configuration"


def test_dynamic_batch_size_adjustment(batch_operation):
    """
    Test dynamic adjustment of batch size based on performance.

    Given: A batch operation processing multiple batches
    When: Processing performance metrics are collected
    Then: Batch size should be adjusted according to performance patterns
    """
    initial_size = batch_operation.batch_size

    # Process multiple batches to trigger adjustments
    for i in range(3):
        items = [{"id": str(j)} for j in range(50)]
        batch_operation.execute_batch(items)

    final_size = batch_operation.batch_size
    assert final_size != initial_size, "Batch size should be dynamically adjusted"


def test_error_rate_impact(batch_operation):
    """
    Test batch size adjustment in response to error rates.

    Given: A batch operation encountering errors
    When: Error rate exceeds threshold
    Then: Batch size should be reduced to improve reliability
    """
    initial_size = batch_operation.batch_size

    # Simulate high error rate
    batch_operation.performance_tracker.record_error_rate(0.4)  # 40% error rate

    # Process a batch to trigger adjustment
    items = [{"id": str(i)} for i in range(50)]
    batch_operation.execute_batch(items)

    assert batch_operation.batch_size < initial_size, "High error rate should reduce batch size"


def test_throughput_optimization(batch_operation):
    """
    Test batch size optimization for maximum throughput.

    Given: A batch operation processing items
    When: Multiple batches are processed with different sizes
    Then: System should converge on optimal batch size for throughput
    """
    # Process batches of different sizes
    sizes = [10, 50, 100, 200]
    throughputs = []

    for size in sizes:
        start_time = time.time()
        items = [{"id": str(i)} for i in range(size)]
        batch_operation.execute_batch(items)
        duration = time.time() - start_time
        throughputs.append(size / duration)

    # Verify throughput improvements
    assert len(set(throughputs)) > 1, "Should observe varying throughput with different batch sizes"


@patch("src.api.repositories.weaviate.metrics.BatchPerformanceTracker.get_optimal_batch_size")
def test_gradual_size_adjustment(mock_get_optimal, batch_operation):
    """
    Test gradual adjustment of batch size to prevent performance spikes.

    Given: A batch operation with performance history
    When: Optimal batch size changes significantly
    Then: Adjustments should be made gradually
    """
    initial_size = batch_operation.batch_size
    mock_get_optimal.return_value = initial_size * 2

    # Process multiple batches to observe gradual changes
    for i in range(5):
        items = [{"id": str(j)} for j in range(50)]
        batch_operation.execute_batch(items)

        # Verify each adjustment is within reasonable bounds
        size_change = abs(batch_operation.batch_size - initial_size)
        assert size_change <= initial_size * 0.5, "Batch size changes should be gradual"


def test_performance_metrics_tracking(batch_operation):
    """
    Test comprehensive tracking of performance metrics.

    Given: A batch operation processing items
    When: Multiple batches are processed
    Then: Performance metrics should be accurately tracked
    """
    items = [{"id": str(i)} for i in range(100)]

    # Process batch and verify metrics
    batch_operation.execute_batch(items)

    metrics = batch_operation.performance_tracker.get_metrics()
    assert "throughput" in metrics, "Should track throughput"
    assert "error_rate" in metrics, "Should track error rate"
    assert "batch_sizes" in metrics, "Should track batch sizes"
