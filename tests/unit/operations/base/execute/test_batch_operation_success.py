"""Test successful batch operation execution."""

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


def test_execute_batch_processes_valid_items(batch_operation):
    """
    Test execute_batch successfully processes valid items.

    Given: A batch of valid items
    When: execute_batch is called
    Then: All items are processed successfully
    """
    items = [{"id": "1", "valid": True}, {"id": "2", "valid": True}]
    results = batch_operation.execute_batch(items)

    assert len(results) == 2
    assert all(r["status"] == "success" for r in results)


def test_execute_batch_processes_partial_batch(batch_operation):
    """
    Test execute_batch handles partial batches.

    Given: A batch smaller than batch_size
    When: execute_batch is called
    Then: Items are processed correctly
    """
    items = [{"id": "1", "valid": True}]
    results = batch_operation.execute_batch(items)

    assert len(results) == 1
    assert results[0]["status"] == "success"


def test_execute_batch_with_empty_batch(batch_operation):
    """
    Test execute_batch with empty batch.

    Given: An empty batch of items
    When: execute_batch is called
    Then: Empty result list is returned
    """
    results = batch_operation.execute_batch([])
    assert len(results) == 0
