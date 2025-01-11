"""Test error handling scenarios of IndexOperation."""

from unittest.mock import Mock

import pytest

from src.api.repositories.weaviate.operations.index import IndexOperation

# Test data constants
TEST_DOCUMENT = {"id": "1", "text": "Sample text", "metadata": {"source": "test"}}


@pytest.fixture
def mock_collection():
    """Setup mock Weaviate collection."""
    collection = Mock()
    collection.batch.add_object.return_value = {"status": "SUCCESS"}
    return collection


@pytest.fixture
def mock_vector_service():
    """Setup mock vector service."""
    service = Mock()
    service.encode.return_value = [[0.1, 0.2, 0.3]]
    return service


@pytest.fixture
def index_operation(mock_collection, mock_vector_service):
    """Setup IndexOperation instance with mocked dependencies."""
    return IndexOperation(vector_service=mock_vector_service, collection=mock_collection)


def test_handle_connection_error(index_operation, mock_collection):
    """
    Test handling of connection errors.

    Given: A connection error occurs during batch processing
    When: Processing the batch
    Then: Should handle connection error appropriately
    """
    mock_collection.batch.add_object.side_effect = ConnectionError("Connection failed")

    result = index_operation.execute_batch([TEST_DOCUMENT])

    assert result.success is False
    assert result.error_count == 1
    assert "Connection failed" in str(result.failed_items[0]["error"])


def test_handle_timeout_error(index_operation, mock_collection):
    """
    Test handling of timeout errors.

    Given: A timeout occurs during batch processing
    When: Processing the batch
    Then: Should handle timeout appropriately
    """
    mock_collection.batch.add_object.side_effect = TimeoutError("Operation timed out")

    result = index_operation.execute_batch([TEST_DOCUMENT])

    assert result.success is False
    assert result.error_count == 1
    assert "Operation timed out" in str(result.failed_items[0]["error"])


def test_handle_authentication_error(index_operation, mock_collection):
    """
    Test handling of authentication errors.

    Given: An authentication error occurs
    When: Processing the batch
    Then: Should handle authentication failure appropriately
    """
    mock_collection.batch.add_object.side_effect = Exception("Authentication failed")

    result = index_operation.execute_batch([TEST_DOCUMENT])

    assert result.success is False
    assert result.error_count == 1
    assert "Authentication failed" in str(result.failed_items[0]["error"])


def test_handle_rate_limit_error(index_operation, mock_collection):
    """
    Test handling of rate limit errors.

    Given: A rate limit error occurs
    When: Processing the batch
    Then: Should handle rate limiting appropriately
    """
    mock_collection.batch.add_object.side_effect = Exception("Rate limit exceeded")

    result = index_operation.execute_batch([TEST_DOCUMENT])

    assert result.success is False
    assert result.error_count == 1
    assert "Rate limit exceeded" in str(result.failed_items[0]["error"])


def test_handle_schema_validation_error(index_operation, mock_collection):
    """
    Test handling of schema validation errors.

    Given: A schema validation error occurs
    When: Processing the batch
    Then: Should handle schema validation failure appropriately
    """
    mock_collection.batch.add_object.side_effect = Exception("Schema validation failed")

    result = index_operation.execute_batch([TEST_DOCUMENT])

    assert result.success is False
    assert result.error_count == 1
    assert "Schema validation failed" in str(result.failed_items[0]["error"])
