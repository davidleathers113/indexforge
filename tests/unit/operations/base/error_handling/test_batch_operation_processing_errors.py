"""Test batch operation processing error handling."""

from unittest.mock import Mock

import pytest
from weaviate.collections import Collection

from src.api.repositories.weaviate.operations.base import BatchOperation


class TestBatchOperation(BatchOperation):
    """Test implementation of BatchOperation."""

    def prepare_item(self, item):
        if item.get("fail_prepare"):
            raise ValueError("Preparation failed")
        return {"prepared": item}

    def validate_item(self, item):
        return "valid" in item

    def process_batch(self, batch):
        if any(item.get("fail_process") for item in batch):
            raise RuntimeError("Processing failed")
        return [{"id": item.get("id", "unknown"), "status": "success"} for item in batch]


@pytest.fixture
def mock_collection():
    """Setup mock collection."""
    return Mock(spec=Collection)


@pytest.fixture
def batch_operation(mock_collection):
    """Setup test batch operation."""
    return TestBatchOperation(collection=mock_collection, batch_size=2)


def test_execute_batch_handles_preparation_error(batch_operation):
    """
    Test error handling during item preparation.

    Given: An item that fails preparation
    When: execute_batch is called
    Then: Preparation error is propagated
    """
    items = [{"id": "1", "valid": True, "fail_prepare": True}]

    with pytest.raises(ValueError, match="Preparation failed"):
        batch_operation.execute_batch(items)


def test_execute_batch_handles_processing_error(batch_operation):
    """
    Test error handling during batch processing.

    Given: A batch that fails processing
    When: execute_batch is called
    Then: Processing error is propagated
    """
    items = [{"id": "1", "valid": True, "fail_process": True}]

    with pytest.raises(RuntimeError, match="Processing failed"):
        batch_operation.execute_batch(items)


def test_execute_batch_handles_mixed_errors(batch_operation):
    """
    Test handling of mixed error types.

    Given: A batch with both validation and processing errors
    When: execute_batch is called
    Then: Errors are handled appropriately
    """
    items = [
        {"id": "1"},  # Validation error
        {"id": "2", "valid": True, "fail_process": True},  # Processing error
    ]

    with pytest.raises(RuntimeError, match="Processing failed"):
        batch_operation.execute_batch(items)
