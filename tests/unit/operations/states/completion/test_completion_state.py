"""Test completion state behavior."""

from unittest.mock import Mock, patch

import pytest
from weaviate.collections import Collection

from src.api.repositories.weaviate.operations.base import BatchOperation
from src.api.repositories.weaviate.operations.states import CompletionState


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


def test_completion_state_records_success_metrics(batch_operation):
    """
    Test success metrics recording.

    Given: A batch operation with successful results
    When: Process is called
    Then: Success metrics are recorded correctly
    """
    state = CompletionState()
    items = [{"id": "1", "status": "success"}, {"id": "2", "status": "success"}]

    with patch.object(batch_operation.performance_tracker, "end_batch") as mock_end:
        results = state.process(batch_operation, items)
        mock_end.assert_called_once_with(successful_objects=2, failed_objects=0)
        assert results == items


def test_completion_state_records_mixed_metrics(batch_operation):
    """
    Test mixed success/failure metrics recording.

    Given: A batch operation with mixed results
    When: Process is called
    Then: Mixed metrics are recorded correctly
    """
    state = CompletionState()
    items = [{"id": "1", "status": "success"}, {"id": "2", "status": "error"}]

    with patch.object(batch_operation.performance_tracker, "end_batch") as mock_end:
        results = state.process(batch_operation, items)
        mock_end.assert_called_once_with(successful_objects=1, failed_objects=1)
        assert results == items


def test_completion_state_handles_empty_batch(batch_operation):
    """
    Test empty batch handling.

    Given: A batch operation with no results
    When: Process is called
    Then: Empty batch is handled correctly
    """
    state = CompletionState()
    items = []

    with patch.object(batch_operation.performance_tracker, "end_batch") as mock_end:
        results = state.process(batch_operation, items)
        mock_end.assert_called_once_with(successful_objects=0, failed_objects=0)
        assert results == items
