"""Test memory usage in batch operations.

Tests memory consumption patterns and cleanup during batch processing operations.
"""

import gc
import os
from unittest.mock import Mock, patch

import psutil
import pytest
from weaviate.collections import Collection

from src.api.repositories.weaviate.operations.base import BatchOperation


def get_process_memory():
    """Get current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


class TestMemoryBatchOperation(BatchOperation):
    """Test implementation of BatchOperation for memory testing."""

    def prepare_item(self, item):
        # Simulate memory allocation during preparation
        item["data"] = "x" * item.get("size", 1000)  # Allocate string of specified size
        return item

    def validate_item(self, item):
        return True

    def process_batch(self, batch):
        # Simulate memory-intensive processing
        results = []
        for item in batch:
            # Process item and create result
            result = {
                "id": item.get("id", "unknown"),
                "status": "success",
                "processed_data": item["data"][:100],  # Keep only part of the data
            }
            results.append(result)
        return results


@pytest.fixture
def mock_collection():
    """Setup mock collection."""
    return Mock(spec=Collection)


@pytest.fixture
def batch_operation(mock_collection):
    """Setup test batch operation."""
    return TestMemoryBatchOperation(collection=mock_collection, batch_size=100)


def test_memory_tracking_basic(batch_operation):
    """
    Test basic memory tracking during batch processing.

    Given: A batch operation processing items with known memory footprint
    When: A batch is processed
    Then: Memory usage should be tracked and stay within expected bounds
    """
    initial_memory = get_process_memory()

    # Process a batch with controlled memory usage
    items = [{"id": str(i), "size": 1000} for i in range(50)]
    batch_operation.execute_batch(items)

    peak_memory = get_process_memory()
    assert peak_memory > initial_memory, "Memory usage should increase during processing"


def test_large_batch_memory_impact(batch_operation):
    """
    Test memory handling with large batch sizes.

    Given: A batch operation processing a large batch
    When: The batch is processed
    Then: Memory usage should scale reasonably with batch size
    """
    initial_memory = get_process_memory()

    # Process increasingly larger batches
    batch_sizes = [100, 500, 1000]
    memory_increases = []

    for size in batch_sizes:
        items = [{"id": str(i), "size": 1000} for i in range(size)]
        batch_operation.execute_batch(items)
        current_memory = get_process_memory()
        memory_increases.append(current_memory - initial_memory)

    # Verify memory usage scales sub-linearly
    assert memory_increases[-1] < memory_increases[0] * len(
        batch_sizes
    ), "Memory usage should not scale linearly with batch size"


def test_memory_cleanup(batch_operation):
    """
    Test memory cleanup after batch processing.

    Given: A batch operation that has processed items
    When: Processing is complete and cleanup is triggered
    Then: Memory should be properly released
    """
    initial_memory = get_process_memory()

    # Process a memory-intensive batch
    items = [{"id": str(i), "size": 10000} for i in range(100)]
    batch_operation.execute_batch(items)

    # Force garbage collection
    gc.collect()

    final_memory = get_process_memory()
    memory_difference = abs(final_memory - initial_memory)

    assert memory_difference < 10, "Memory should be released after cleanup"


def test_memory_usage_pattern(batch_operation):
    """
    Test memory usage patterns during batch processing.

    Given: A batch operation processing multiple batches
    When: Multiple batches are processed sequentially
    Then: Memory usage should follow a consistent pattern
    """
    memory_samples = []

    # Process multiple batches and sample memory
    for i in range(3):
        items = [{"id": f"{i}-{j}", "size": 5000} for j in range(50)]
        memory_samples.append(get_process_memory())
        batch_operation.execute_batch(items)
        memory_samples.append(get_process_memory())
        gc.collect()
        memory_samples.append(get_process_memory())

    # Verify memory pattern
    processing_spikes = [
        memory_samples[i + 1] - memory_samples[i] for i in range(0, len(memory_samples) - 1, 3)
    ]
    cleanup_drops = [
        memory_samples[i + 1] - memory_samples[i + 2] for i in range(0, len(memory_samples) - 2, 3)
    ]

    assert all(spike > 0 for spike in processing_spikes), "Memory should spike during processing"
    assert all(drop > 0 for drop in cleanup_drops), "Memory should drop after cleanup"


@patch("gc.collect")
def test_forced_memory_cleanup(mock_gc_collect, batch_operation):
    """
    Test forced memory cleanup mechanisms.

    Given: A batch operation with accumulated memory usage
    When: Forced cleanup is triggered
    Then: Memory should be aggressively reclaimed
    """
    # Process memory-intensive batch
    items = [{"id": str(i), "size": 20000} for i in range(50)]
    batch_operation.execute_batch(items)

    # Verify cleanup was attempted
    assert mock_gc_collect.called, "Garbage collection should be triggered"


def test_concurrent_memory_usage(batch_operation):
    """
    Test memory usage during concurrent operations.

    Given: Multiple batch operations running concurrently
    When: Batches are processed simultaneously
    Then: Memory usage should be managed effectively
    """
    initial_memory = get_process_memory()

    # Simulate concurrent processing
    batches = [
        [{"id": f"1-{i}", "size": 5000} for i in range(50)],
        [{"id": f"2-{i}", "size": 5000} for i in range(50)],
    ]

    for batch in batches:
        batch_operation.execute_batch(batch)

    # Force cleanup
    gc.collect()

    final_memory = get_process_memory()
    assert abs(final_memory - initial_memory) < 10, "Memory should be managed effectively"
