"""Test batch operation validation error handling."""

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


def test_execute_batch_handles_missing_valid_field(batch_operation):
    """
    Test validation failure when valid field is missing.

    Given: An item missing the valid field
    When: execute_batch is called
    Then: Item is marked as validation error
    """
    items = [{"id": "1"}]  # Missing valid field
    results = batch_operation.execute_batch(items)

    assert len(results) == 1
    assert results[0]["status"] == "error"
    assert "Validation failed" in results[0]["error"]


def test_execute_batch_handles_explicit_invalid_item(batch_operation):
    """
    Test validation failure with explicitly invalid item.

    Given: An item with valid=False
    When: execute_batch is called
    Then: Item is marked as validation error
    """
    items = [{"id": "1", "valid": False}]
    results = batch_operation.execute_batch(items)

    assert len(results) == 1
    assert results[0]["status"] == "error"
    assert "Validation failed" in results[0]["error"]


def test_execute_batch_handles_none_valid_value(batch_operation):
    """
    Test validation failure with None value.

    Given: An item with valid=None
    When: execute_batch is called
    Then: Item is marked as validation error
    """
    items = [{"id": "1", "valid": None}]
    results = batch_operation.execute_batch(items)

    assert len(results) == 1
    assert results[0]["status"] == "error"
    assert "Validation failed" in results[0]["error"]
