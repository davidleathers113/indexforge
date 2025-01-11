"""Test batch operation size handling."""

from unittest.mock import Mock

import pytest
from weaviate.collections import Collection

from src.api.repositories.weaviate.operations.base import BatchOperation


class TestBatchOperation(BatchOperation):
    """Test implementation of BatchOperation."""

    def prepare_item(self, item):
        return {"prepared": item}

    def validate_item(self, item):
        return "valid" in item

    def process_batch(self, batch):
        return [{"id": item.get("id", "unknown"), "status": "success"} for item in batch]


@pytest.fixture
def mock_collection():
    """Setup mock collection."""
    return Mock(spec=Collection)


@pytest.fixture
def batch_operation(mock_collection):
    """Setup test batch operation."""
    return TestBatchOperation(collection=mock_collection, batch_size=2)


def test_execute_batch_respects_batch_size(batch_operation):
    """
    Test batch size limit is respected.

    Given: A batch larger than batch_size
    When: execute_batch is called
    Then: Items are processed in correct batch sizes
    """
    batch_size = batch_operation.batch_size
    items = [{"id": str(i), "valid": True} for i in range(batch_size * 3)]

    with Mock() as mock_process:
        batch_operation.process_batch = mock_process
        batch_operation.execute_batch(items)

        # Should be called 3 times with batch_size items each
        assert mock_process.call_count == 3
        for call in mock_process.call_args_list:
            assert len(call[0][0]) <= batch_size


def test_execute_batch_with_minimum_batch_size(batch_operation):
    """
    Test execution with minimum batch size.

    Given: A batch operation configured with minimum batch size
    When: execute_batch is called
    Then: Items are processed correctly
    """
    batch_operation.batch_size = 1
    items = [{"id": "1", "valid": True}, {"id": "2", "valid": True}]

    with Mock() as mock_process:
        batch_operation.process_batch = mock_process
        batch_operation.execute_batch(items)

        # Should be called twice with one item each
        assert mock_process.call_count == 2
        for call in mock_process.call_args_list:
            assert len(call[0][0]) == 1


def test_execute_batch_with_large_batch_size(batch_operation):
    """
    Test execution with large batch size.

    Given: A batch operation configured with large batch size
    When: execute_batch is called with fewer items
    Then: All items are processed in single batch
    """
    batch_operation.batch_size = 100
    items = [{"id": str(i), "valid": True} for i in range(5)]

    with Mock() as mock_process:
        batch_operation.process_batch = mock_process
        batch_operation.execute_batch(items)

        # Should be called once with all items
        assert mock_process.call_count == 1
        assert len(mock_process.call_args[0][0]) == 5
