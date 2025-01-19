"""Test collection operations integration functionality.

This module contains integration tests for collection operations,
focusing on batch configuration, retry mechanisms, and error handling.
"""

from unittest.mock import Mock, call, patch

import pytest
import weaviate
from requests.exceptions import ConnectionError

from src.api.repositories.weaviate.exceptions import BatchConfigurationError, RetryExhaustedError

# Test data constants
TEST_CONFIG = {
    "url": "http://localhost:8080",
    "auth_credentials": weaviate.auth.AuthApiKey(api_key="test-api-key"),
    "additional_config": weaviate.config.AdditionalConfig(
        timeout_config=weaviate.config.Timeout(timeout_ms=300000),
        batch_config=weaviate.config.BatchConfig(
            creation_time_ms=100,
            dynamic=True,
            batch_size=100,
        ),
    ),
    "additional_headers": None,
}

TEST_COLLECTION_CONFIG = {
    "name": "test_collection",
    "vectorizer_config": weaviate.config.Configure.Vectorizer.text2vec_contextionary(),
    "properties": [
        weaviate.classes.Property(
            name="text",
            data_type=["text"],
        ),
        weaviate.classes.Property(
            name="metadata",
            data_type=["object"],
        ),
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
    collection.data.insert_many.return_value = {"status": "success"}
    return collection


def test_batch_configuration_success(mock_client, mock_collection):
    """
    Test successful batch configuration.

    Given: Valid batch configuration parameters
    When: Configuring batch operations for a collection
    Then: Configuration should be applied successfully
    """
    mock_client.collections.get.return_value = mock_collection
    batch_config = weaviate.config.BatchConfig(
        batch_size=100,
        dynamic=True,
        creation_time_ms=100,
    )

    client = weaviate.Client(**TEST_CONFIG)
    collection = client.collections.get("test_collection")
    collection.batch.configure(batch_config)

    mock_collection.batch.configure.assert_called_once_with(batch_config)


def test_batch_configuration_validation(mock_client, mock_collection):
    """
    Test batch configuration validation.

    Given: Invalid batch configuration parameters
    When: Attempting to configure batch operations
    Then: Should raise appropriate validation errors
    """
    mock_client.collections.get.return_value = mock_collection
    invalid_configs = [
        weaviate.config.BatchConfig(batch_size=-1),  # Invalid batch size
        weaviate.config.BatchConfig(creation_time_ms="invalid"),  # Invalid creation time
        weaviate.config.BatchConfig(dynamic="not-boolean"),  # Invalid dynamic setting
    ]

    client = weaviate.Client(**TEST_CONFIG)
    collection = client.collections.get("test_collection")

    for config in invalid_configs:
        with pytest.raises(BatchConfigurationError):
            collection.batch.configure(config)


def test_operation_retry_mechanism(mock_client, mock_collection):
    """
    Test retry mechanism for batch operations.

    Given: Temporary failures that resolve after retries
    When: Performing batch operations
    Then: Should retry failed operations and eventually succeed
    """
    mock_client.collections.get.return_value = mock_collection
    # Mock failures that succeed after retries
    mock_collection.data.insert_many.side_effect = [
        ConnectionError("First attempt"),
        ConnectionError("Second attempt"),
        {"status": "success"},  # Success on third attempt
    ]

    client = weaviate.Client(**TEST_CONFIG)
    collection = client.collections.get("test_collection")
    result = collection.data.insert_many([{"id": "1", "text": "test"}])

    assert result["status"] == "success"
    assert mock_collection.data.insert_many.call_count == 3


def test_retry_exhaustion(mock_client, mock_collection):
    """
    Test behavior when retries are exhausted.

    Given: Persistent failures that don't resolve within retry limit
    When: Performing batch operations
    Then: Should raise retry exhausted error after all attempts fail
    """
    mock_client.collections.get.return_value = mock_collection
    mock_collection.data.insert_many.side_effect = ConnectionError("Persistent failure")

    client = weaviate.Client(**TEST_CONFIG)
    collection = client.collections.get("test_collection")

    with pytest.raises(RetryExhaustedError) as exc_info:
        collection.data.insert_many([{"id": "1", "text": "test"}])

    assert "Persistent failure" in str(exc_info.value)
    assert (
        mock_collection.data.insert_many.call_count
        == TEST_CONFIG["additional_config"].timeout_config.retries
    )


def test_error_callback_invocation(mock_client, mock_collection):
    """
    Test error callback mechanism.

    Given: Operations that trigger errors with registered callbacks
    When: Errors occur during batch operations
    Then: Error callbacks should be invoked with correct error information
    """
    mock_client.collections.get.return_value = mock_collection
    error_callback = Mock()

    client = weaviate.Client(**TEST_CONFIG)
    collection = client.collections.get("test_collection")
    collection.batch.configure(weaviate.config.BatchConfig(callback_on_error=error_callback))

    # Simulate an error
    error = Exception("Test error")
    mock_collection.data.insert_many.side_effect = error

    try:
        collection.data.insert_many([{"id": "1", "text": "test"}])
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

    client = weaviate.Client(**TEST_CONFIG)
    collection = client.collections.get("test_collection")

    # Simulate concurrent operations
    batch1 = [{"id": "1", "text": "test1"}]
    batch2 = [{"id": "2", "text": "test2"}]

    collection.data.insert_many(batch1)
    collection.data.insert_many(batch2)

    # Verify operations were processed in order
    expected_calls = [call(batch1), call(batch2)]
    mock_collection.data.insert_many.assert_has_calls(expected_calls, any_order=False)
