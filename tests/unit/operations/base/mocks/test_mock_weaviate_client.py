"""Test Weaviate client operations using mocks.

Tests system behavior with mocked Weaviate client to validate operations,
error handling, timeouts, and retry mechanisms.
"""

from unittest.mock import Mock, patch

import pytest
from weaviate.collections import Collection
from weaviate.exceptions import WeaviateConnectionError, WeaviateRequestError, WeaviateTimeoutError

from src.api.repositories.weaviate.operations.base import BatchOperation


class TestMockBatchOperation(BatchOperation):
    """Test implementation of BatchOperation for mock testing."""

    def prepare_item(self, item):
        if item.get("invalid"):
            raise ValueError("Invalid item")
        return {"prepared": item}

    def validate_item(self, item):
        return not item.get("invalid")

    def process_batch(self, batch):
        return self.collection.batch.add_objects(batch)


@pytest.fixture
def mock_collection():
    """Setup mock Weaviate collection."""
    collection = Mock(spec=Collection)
    collection.batch = Mock()
    collection.batch.add_objects = Mock()
    return collection


@pytest.fixture
def batch_operation(mock_collection):
    """Setup test batch operation with mocked collection."""
    return TestMockBatchOperation(collection=mock_collection, batch_size=2)


def test_successful_batch_operation(batch_operation):
    """
    Test successful batch operation with mocked client.

    Given: A batch operation with mocked Weaviate collection
    When: A valid batch is processed
    Then: The operation completes successfully with expected results
    """
    # Setup mock response
    batch_operation.collection.batch.add_objects.return_value = [
        {"id": "1", "status": "success"},
        {"id": "2", "status": "success"},
    ]

    items = [{"id": "1"}, {"id": "2"}]
    results = batch_operation.execute_batch(items)

    assert len(results) == 2, "Should process all items"
    assert all(r["status"] == "success" for r in results), "All operations should succeed"
    batch_operation.collection.batch.add_objects.assert_called_once()


def test_connection_error_handling(batch_operation):
    """
    Test handling of connection errors.

    Given: A batch operation where the client throws connection errors
    When: A batch is processed
    Then: The error is caught and properly handled
    """
    batch_operation.collection.batch.add_objects.side_effect = WeaviateConnectionError(
        "Connection failed"
    )

    items = [{"id": "1"}, {"id": "2"}]
    with pytest.raises(WeaviateConnectionError, match="Connection failed"):
        batch_operation.execute_batch(items)


def test_timeout_handling(batch_operation):
    """
    Test handling of timeout errors.

    Given: A batch operation where operations timeout
    When: A batch is processed
    Then: Timeout errors are properly handled
    """
    batch_operation.collection.batch.add_objects.side_effect = WeaviateTimeoutError(
        "Operation timed out"
    )

    items = [{"id": "1"}, {"id": "2"}]
    with pytest.raises(WeaviateTimeoutError, match="Operation timed out"):
        batch_operation.execute_batch(items)


@patch("src.api.repositories.weaviate.retry.RetryStrategy.should_retry")
def test_retry_logic(mock_should_retry, batch_operation):
    """
    Test retry mechanism for failed operations.

    Given: A batch operation that fails initially but succeeds on retry
    When: A batch is processed
    Then: The operation is retried and eventually succeeds
    """
    # Setup mock to fail twice then succeed
    batch_operation.collection.batch.add_objects.side_effect = [
        WeaviateConnectionError("First attempt"),
        WeaviateConnectionError("Second attempt"),
        [{"id": "1", "status": "success"}, {"id": "2", "status": "success"}],
    ]

    # Configure retry strategy to allow 2 retries
    mock_should_retry.side_effect = [True, True, False]

    items = [{"id": "1"}, {"id": "2"}]
    results = batch_operation.execute_batch(items)

    assert len(results) == 2, "Should eventually process all items"
    assert batch_operation.collection.batch.add_objects.call_count == 3, "Should retry twice"


def test_invalid_request_handling(batch_operation):
    """
    Test handling of invalid request errors.

    Given: A batch operation with invalid input
    When: The batch is processed
    Then: The error is properly handled and reported
    """
    batch_operation.collection.batch.add_objects.side_effect = WeaviateRequestError(
        "Invalid request", status_code=400
    )

    items = [{"id": "1"}, {"id": "2"}]
    with pytest.raises(WeaviateRequestError, match="Invalid request"):
        batch_operation.execute_batch(items)


def test_partial_success_handling(batch_operation):
    """
    Test handling of partially successful operations.

    Given: A batch operation where some items succeed and others fail
    When: The batch is processed
    Then: Successes and failures are properly tracked
    """
    batch_operation.collection.batch.add_objects.return_value = [
        {"id": "1", "status": "success"},
        {"id": "2", "status": "failed", "error": "Processing error"},
    ]

    items = [{"id": "1"}, {"id": "2"}]
    results = batch_operation.execute_batch(items)

    assert len(results) == 2, "Should return results for all items"
    assert results[0]["status"] == "success"
    assert results[1]["status"] == "failed"


@patch("time.sleep")  # Prevent actual waiting in tests
def test_retry_backoff(mock_sleep, batch_operation):
    """
    Test retry backoff mechanism.

    Given: A batch operation that requires multiple retries
    When: The operation fails multiple times
    Then: Backoff delays are properly implemented
    """
    # Setup mock to fail repeatedly
    batch_operation.collection.batch.add_objects.side_effect = WeaviateConnectionError(
        "Connection failed"
    )

    items = [{"id": "1"}, {"id": "2"}]
    with pytest.raises(WeaviateConnectionError):
        batch_operation.execute_batch(items)

    # Verify increasing delays between retries
    assert mock_sleep.call_count > 0, "Should implement backoff delays"
    delays = [call[0][0] for call in mock_sleep.call_args_list]
    assert all(delays[i] <= delays[i + 1] for i in range(len(delays) - 1)), "Delays should increase"
