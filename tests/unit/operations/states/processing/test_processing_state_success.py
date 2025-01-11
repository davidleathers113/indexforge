"""Test successful processing state behavior."""

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
        return [{"id": item["id"], "status": "success"} for item in batch]


@pytest.fixture
def mock_collection():
    """Setup mock collection."""
    return Mock(spec=Collection)


@pytest.fixture
def batch_operation(mock_collection):
    """Setup test batch operation."""
    return TestBatchOperation(collection=mock_collection)


def test_processing_state_configures_batch(batch_operation):
    """
    Test batch configuration.

    Given: A batch operation in processing state
    When: Process is called
    Then: Batch is configured correctly
    """
    state = ProcessingState()
    items = [{"id": "1"}, {"id": "2"}]

    with patch.object(batch_operation.collection, "batch") as mock_batch:
        mock_batch.__enter__.return_value = mock_batch
        state.process(batch_operation, items)

        mock_batch.configure.assert_called_once()
        config = mock_batch.configure.call_args[1]
        assert config["batch_size"] == len(items)
        assert config["dynamic"] is True
        assert config["timeout_retries"] == 3


def test_processing_state_records_completion(batch_operation):
    """
    Test completion recording.

    Given: A batch operation in processing state
    When: Process completes successfully
    Then: Batch completion is recorded
    """
    state = ProcessingState()
    items = [{"id": "1"}, {"id": "2"}]

    with patch.object(batch_operation.collection, "batch") as mock_batch:
        mock_batch.__enter__.return_value = mock_batch
        state.process(batch_operation, items)

        batch_operation.metrics.record_batch_completion.assert_called_once()


def test_processing_state_handles_empty_batch(batch_operation):
    """
    Test empty batch handling.

    Given: A batch operation in processing state
    When: Process is called with empty batch
    Then: Empty batch is handled correctly
    """
    state = ProcessingState()
    items = []

    with patch.object(batch_operation.collection, "batch") as mock_batch:
        mock_batch.__enter__.return_value = mock_batch
        results = state.process(batch_operation, items)

        assert len(results) == 0
        mock_batch.configure.assert_called_once()
