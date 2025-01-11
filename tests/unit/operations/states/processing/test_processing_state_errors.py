"""Test processing state error handling."""

from unittest.mock import Mock, patch

import pytest
from weaviate.collections import Collection

from src.api.repositories.weaviate.operations.base import BatchOperation
from src.api.repositories.weaviate.operations.states import ProcessingState


class TestBatchOperation(BatchOperation):
    """Test implementation of BatchOperation."""

    def prepare_item(self, item):
        return item

    def validate_item(self, item):
        return True

    def process_batch(self, batch):
        if any(item.get("fail") for item in batch):
            raise RuntimeError("Processing failed")
        return [{"id": item["id"], "status": "success"} for item in batch]


@pytest.fixture
def mock_collection():
    """Setup mock collection."""
    return Mock(spec=Collection)


@pytest.fixture
def batch_operation(mock_collection):
    """Setup test batch operation."""
    return TestBatchOperation(collection=mock_collection)


def test_processing_state_handles_configuration_error(batch_operation):
    """
    Test batch configuration error handling.

    Given: A batch operation that fails during configuration
    When: Process is called
    Then: Configuration error is propagated
    """
    state = ProcessingState()
    items = [{"id": "1"}, {"id": "2"}]

    with patch.object(batch_operation.collection, "batch") as mock_batch:
        mock_batch.__enter__.return_value = mock_batch
        mock_batch.configure.side_effect = ValueError("Invalid configuration")

        with pytest.raises(ValueError, match="Invalid configuration"):
            state.process(batch_operation, items)


def test_processing_state_handles_batch_context_error(batch_operation):
    """
    Test batch context error handling.

    Given: A batch operation that fails to enter context
    When: Process is called
    Then: Context error is propagated
    """
    state = ProcessingState()
    items = [{"id": "1"}, {"id": "2"}]

    with patch.object(batch_operation.collection, "batch") as mock_batch:
        mock_batch.__enter__.side_effect = RuntimeError("Context failed")

        with pytest.raises(RuntimeError, match="Context failed"):
            state.process(batch_operation, items)


def test_processing_state_handles_add_object_error(batch_operation):
    """
    Test object addition error handling.

    Given: A batch operation where adding object fails
    When: Process is called
    Then: Add object error is handled
    """
    state = ProcessingState()
    items = [{"id": "1"}, {"id": "2"}]

    with patch.object(batch_operation.collection, "batch") as mock_batch:
        mock_batch.__enter__.return_value = mock_batch
        mock_batch.add_object.side_effect = Exception("Add failed")

        results = state.process(batch_operation, items)
        assert len(results) == 2
        assert all(r["status"] == "error" for r in results)
        assert all("Add failed" in r["error"] for r in results)
