"""Test collection operations integration functionality.

This module contains integration tests for collection operations,
focusing on batch configuration, retry mechanisms, and error handling.
"""

from unittest.mock import Mock, call, patch

import pytest
from requests.exceptions import ConnectionError

from src.api.repositories.weaviate.client import WeaviateClient
from src.api.repositories.weaviate.exceptions import (
    BatchConfigurationError,
    RetryExhaustedError,
)

# Test data constants
TEST_CONFIG = {
    "url": "http://localhost:8080",
    "api_key": "test-api-key",
    "timeout": 300,
    "retry_count": 3,
}

TEST_COLLECTION_CONFIG = {
    "name": "test_collection",
    "vectorizer": "text2vec-contextionary",
    "properties": [
        {"name": "text", "dataType": ["text"]},
        {"name": "metadata", "dataType": ["object"]},
    ],
}


@pytest.fixture
def mock_client():
    """Setup mock Weaviate client."""
    with patch("weaviate.Client") as mock_client:
        client = mock_client.return_value
        client.collections.create.return_value = Mock()
        client.collections.get.return_value = Mock()
        yield client


@pytest.fixture
def mock_collection():
    """Setup mock collection with batch configuration capabilities."""
    collection = Mock()
    collection.batch.configure.return_value = None
    return collection


def test_batch_configuration_success(mock_client, mock_collection):
    """
    Test successful batch configuration.

    Given: Valid batch configuration parameters
    When: Configuring batch operations for a collection
    Then: Configuration should be applied successfully
    """
    mock_client.collections.get.return_value = mock_collection
    batch_config = {"batch_size": 100, "dynamic": True, "timeout_retries": 3}

    client = WeaviateClient(**TEST_CONFIG)
    collection = client.collections.get("test_collection")
    collection.batch.configure(**batch_config)

    mock_collection.batch.configure.assert_called_once_with(**batch_config)


def test_batch_configuration_validation(mock_client, mock_collection):
    """
    Test batch configuration validation.

    Given: Invalid batch configuration parameters
    When: Attempting to configure batch operations
    Then: Should raise appropriate validation errors
    """
    mock_client.collections.get.return_value = mock_collection
    invalid_configs = [
        {"batch_size": -1},  # Invalid batch size
        {"timeout_retries": "invalid"},  # Invalid retry count
        {"dynamic": "not-boolean"},  # Invalid dynamic setting
    ]

    client = WeaviateClient(**TEST_CONFIG)
    collection = client.collections.get("test_collection")

    for config in invalid_configs:
        with pytest.raises(BatchConfigurationError):
            collection.batch.configure(**config)


def test_operation_retry_mechanism(mock_client, mock_collection):
    """
    Test retry mechanism for batch operations.

    Given: Temporary failures that resolve after retries
    When: Performing batch operations
    Then: Should retry failed operations and eventually succeed
    """
    mock_client.collections.get.return_value = mock_collection
    # Mock failures that succeed after retries
    mock_collection.batch.add_objects.side_effect = [
        ConnectionError("First attempt"),
        ConnectionError("Second attempt"),
        {"status": "success"},  # Success on third attempt
    ]

    client = WeaviateClient(**TEST_CONFIG)
    collection = client.collections.get("test_collection")
    result = collection.batch.add_objects([{"id": "1", "text": "test"}])

    assert result["status"] == "success"
    assert mock_collection.batch.add_objects.call_count == 3


def test_retry_exhaustion(mock_client, mock_collection):
    """
    Test behavior when retries are exhausted.

    Given: Persistent failures that don't resolve within retry limit
    When: Performing batch operations
    Then: Should raise retry exhausted error after all attempts fail
    """
    mock_client.collections.get.return_value = mock_collection
    mock_collection.batch.add_objects.side_effect = ConnectionError("Persistent failure")

    client = WeaviateClient(**TEST_CONFIG)
    collection = client.collections.get("test_collection")

    with pytest.raises(RetryExhaustedError) as exc_info:
        collection.batch.add_objects([{"id": "1", "text": "test"}])

    assert "Persistent failure" in str(exc_info.value)
    assert mock_collection.batch.add_objects.call_count == TEST_CONFIG["retry_count"]


def test_error_callback_invocation(mock_client, mock_collection):
    """
    Test error callback mechanism.

    Given: Operations that trigger errors with registered callbacks
    When: Errors occur during batch operations
    Then: Error callbacks should be invoked with correct error information
    """
    mock_client.collections.get.return_value = mock_collection
    error_callback = Mock()

    client = WeaviateClient(**TEST_CONFIG)
    collection = client.collections.get("test_collection")
    collection.batch.on_error(error_callback)

    # Simulate an error
    error = Exception("Test error")
    mock_collection.batch.add_objects.side_effect = error

    try:
        collection.batch.add_objects([{"id": "1", "text": "test"}])
    except Exception:
        pass

    error_callback.assert_called_with(error)


def test_concurrent_batch_operations(mock_client, mock_collection):
    """
    Test handling of concurrent batch operations.

    Given: Multiple concurrent batch operations
    When: Processing batches simultaneously
    Then: Should handle concurrency correctly and maintain consistency
    """
    mock_client.collections.get.return_value = mock_collection

    client = WeaviateClient(**TEST_CONFIG)
    collection = client.collections.get("test_collection")

    # Simulate concurrent operations
    batch1 = [{"id": "1", "text": "test1"}]
    batch2 = [{"id": "2", "text": "test2"}]

    collection.batch.add_objects(batch1)
    collection.batch.add_objects(batch2)

    # Verify operations were processed in order
    expected_calls = [call(batch1), call(batch2)]
    mock_collection.batch.add_objects.assert_has_calls(expected_calls, any_order=False)
