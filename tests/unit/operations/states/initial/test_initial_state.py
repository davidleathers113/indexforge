"""Test initial state behavior of batch operations."""

from unittest.mock import Mock, patch

import pytest
from weaviate.collections import Collection

from src.api.repositories.weaviate.operations.base import BatchOperation
from src.api.repositories.weaviate.operations.states import InitialState


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


def test_initial_state_starts_performance_tracking(batch_operation):
    """
    Test performance tracking initialization.

    Given: A batch operation in initial state
    When: Process is called
    Then: Performance tracking is started with correct batch size
    """
    state = InitialState()
    items = [{"id": "1"}, {"id": "2"}]

    with patch.object(batch_operation.performance_tracker, "start_batch") as mock_start:
        state.process(batch_operation, items)
        mock_start.assert_called_once_with(2)


def test_initial_state_returns_unmodified_items(batch_operation):
    """
    Test items are passed through unchanged.

    Given: A batch operation in initial state
    When: Process is called
    Then: Original items are returned unmodified
    """
    state = InitialState()
    items = [{"id": "1"}, {"id": "2"}]

    result = state.process(batch_operation, items)
    assert result == items


def test_initial_state_handles_empty_batch(batch_operation):
    """
    Test empty batch handling.

    Given: A batch operation in initial state
    When: Process is called with empty batch
    Then: Empty batch is handled correctly
    """
    state = InitialState()
    items = []

    with patch.object(batch_operation.performance_tracker, "start_batch") as mock_start:
        result = state.process(batch_operation, items)
        mock_start.assert_called_once_with(0)
        assert result == items
