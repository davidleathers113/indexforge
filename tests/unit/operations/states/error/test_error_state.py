"""Test error state behavior."""

from unittest.mock import Mock, patch

import pytest
from weaviate.collections import Collection

from src.api.repositories.weaviate.operations.base import BatchOperation
from src.api.repositories.weaviate.operations.states import ErrorState


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


def test_error_state_records_batch_error(batch_operation):
    """
    Test batch error recording.

    Given: A batch operation in error state
    When: Process is called
    Then: Batch error is recorded
    """
    state = ErrorState()
    items = [{"id": "1"}, {"id": "2"}]

    with patch.object(batch_operation.metrics, "record_batch_error") as mock_record:
        state.process(batch_operation, items)
        mock_record.assert_called_once()


def test_error_state_records_failure_metrics(batch_operation):
    """
    Test failure metrics recording.

    Given: A batch operation in error state
    When: Process is called
    Then: All items are marked as failed
    """
    state = ErrorState()
    items = [{"id": "1"}, {"id": "2"}]

    with patch.object(batch_operation.performance_tracker, "end_batch") as mock_end:
        state.process(batch_operation, items)
        mock_end.assert_called_once_with(successful_objects=0, failed_objects=2)


def test_error_state_formats_error_results(batch_operation):
    """
    Test error result formatting.

    Given: A batch operation in error state
    When: Process is called
    Then: Results are formatted with error status
    """
    state = ErrorState()
    items = [{"id": "1"}, {"id": "2"}]

    results = state.process(batch_operation, items)

    assert len(results) == 2
    for result in results:
        assert result["status"] == "error"
        assert "Batch operation failed" in result["error"]
        assert "id" in result
