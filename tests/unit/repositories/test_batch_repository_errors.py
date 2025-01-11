"""Test error handling functionality of BatchRepository."""

from unittest.mock import Mock

import pytest

from src.api.repositories.weaviate.exceptions import (
    CollectionError,
    ConnectionError,
)
from src.api.repositories.weaviate.repository import BatchRepository

# Test data constants
TEST_CONFIG = {
    "url": "http://localhost:8080",
    "api_key": "test-api-key",
    "timeout": 300,
    "batch_size": 100,
}

TEST_DOCUMENTS = [
    {"id": "1", "text": "First document", "metadata": {"source": "test"}},
    {"id": "2", "text": "Second document", "metadata": {"source": "test"}},
]


@pytest.fixture
def mock_client():
    """Setup mock Weaviate client."""
    client = Mock()
    client.collections.get.return_value = Mock()
    return client


@pytest.fixture
def mock_collection():
    """Setup mock Weaviate collection."""
    collection = Mock()
    collection.batch.add_objects.return_value = {"status": "SUCCESS"}
    collection.batch.delete_objects.return_value = {"status": "SUCCESS"}
    return collection


@pytest.fixture
def repository(mock_client, mock_collection):
    """Setup BatchRepository instance with mocked dependencies."""
    mock_client.collections.get.return_value = mock_collection
    return BatchRepository(client=mock_client, **TEST_CONFIG)


def test_handle_connection_error(repository, mock_collection):
    """
    Test handling of connection errors.

    Given: A connection error occurs during operation
    When: Performing batch operations
    Then: Should handle connection error appropriately
    """
    mock_collection.batch.add_objects.side_effect = ConnectionError("Connection failed")
    collection_name = "test_collection"

    result = repository.index_documents(collection_name, TEST_DOCUMENTS)

    assert result.success is False
    assert result.error_count == len(TEST_DOCUMENTS)
    assert "Connection failed" in str(result.failed_items[0]["error"])


def test_handle_collection_not_found(repository, mock_client):
    """
    Test handling of collection not found errors.

    Given: Operations on non-existent collection
    When: Attempting batch operations
    Then: Should handle collection not found appropriately
    """
    mock_client.collections.get.side_effect = Exception("Collection not found")
    collection_name = "non_existent"

    with pytest.raises(CollectionError, match="Collection not found"):
        repository.index_documents(collection_name, TEST_DOCUMENTS)


def test_handle_validation_errors(repository, mock_collection):
    """
    Test handling of document validation errors.

    Given: Invalid documents in batch
    When: Attempting to index documents
    Then: Should handle validation errors appropriately
    """
    invalid_documents = [{"missing_required_field": "value"}, {"id": "2", "text": None}, None]
    collection_name = "test_collection"

    result = repository.index_documents(collection_name, invalid_documents)

    assert result.success is False
    assert result.error_count == len(invalid_documents)
    assert all("error" in item for item in result.failed_items)


def test_handle_timeout_error(repository, mock_collection):
    """
    Test handling of timeout errors.

    Given: Operations that timeout
    When: Performing batch operations
    Then: Should handle timeout appropriately
    """
    mock_collection.batch.add_objects.side_effect = TimeoutError("Operation timed out")
    collection_name = "test_collection"

    result = repository.index_documents(collection_name, TEST_DOCUMENTS)

    assert result.success is False
    assert result.error_count == len(TEST_DOCUMENTS)
    assert "Operation timed out" in str(result.failed_items[0]["error"])


def test_handle_batch_size_exceeded(repository, mock_collection):
    """
    Test handling of batch size limit errors.

    Given: Batch exceeding size limits
    When: Attempting batch operations
    Then: Should handle size limit appropriately
    """
    mock_collection.batch.add_objects.side_effect = Exception("Batch size limit exceeded")
    collection_name = "test_collection"
    large_batch = TEST_DOCUMENTS * 1000  # Create artificially large batch

    result = repository.index_documents(collection_name, large_batch)

    assert result.success is False
    assert "Batch size limit exceeded" in str(result.failed_items[0]["error"])
