"""Test error handling functionality of DeleteOperation."""

from unittest.mock import Mock

import pytest

from src.api.repositories.weaviate.exceptions import (
    ConnectionError,
)
from src.api.repositories.weaviate.operations.delete import DeleteOperation


# Test data constants
TEST_DOCUMENT = {"id": "550e8400-e29b-41d4-a716-446655440000"}


@pytest.fixture
def mock_collection():
    """Setup mock Weaviate collection."""
    collection = Mock()
    collection.batch.delete_objects.return_value = {"status": "SUCCESS"}
    return collection


@pytest.fixture
def delete_operation(mock_collection):
    """Setup DeleteOperation instance with mocked dependencies."""
    return DeleteOperation(collection=mock_collection)


def test_handle_connection_error(delete_operation, mock_collection):
    """
    Test handling of connection errors.

    Given: A connection error occurs during deletion
    When: Executing the batch deletion
    Then: Should handle connection error appropriately
    """
    mock_collection.batch.delete_objects.side_effect = ConnectionError("Connection failed")

    result = delete_operation.execute_batch([TEST_DOCUMENT])

    assert result.success is False
    assert result.error_count == 1
    assert "Connection failed" in str(result.failed_items[0]["error"])


def test_handle_timeout_error(delete_operation, mock_collection):
    """
    Test handling of timeout errors.

    Given: A timeout occurs during deletion
    When: Executing the batch deletion
    Then: Should handle timeout appropriately
    """
    mock_collection.batch.delete_objects.side_effect = TimeoutError("Operation timed out")

    result = delete_operation.execute_batch([TEST_DOCUMENT])

    assert result.success is False
    assert result.error_count == 1
    assert "Operation timed out" in str(result.failed_items[0]["error"])


def test_handle_not_found_error(delete_operation, mock_collection):
    """
    Test handling of document not found errors.

    Given: A document does not exist
    When: Attempting to delete the document
    Then: Should handle not found error appropriately
    """
    mock_collection.batch.delete_objects.return_value = {
        "status": "FAILED",
        "error": "Document not found",
    }

    result = delete_operation.execute_batch([TEST_DOCUMENT])

    assert result.success is False
    assert result.error_count == 1
    assert "Document not found" in str(result.failed_items[0]["error"])


def test_handle_permission_error(delete_operation, mock_collection):
    """
    Test handling of permission errors.

    Given: User lacks permission to delete
    When: Attempting to delete documents
    Then: Should handle permission error appropriately
    """
    mock_collection.batch.delete_objects.side_effect = Exception("Permission denied")

    result = delete_operation.execute_batch([TEST_DOCUMENT])

    assert result.success is False
    assert result.error_count == 1
    assert "Permission denied" in str(result.failed_items[0]["error"])


def test_handle_validation_error(delete_operation):
    """
    Test handling of validation errors.

    Given: Invalid documents in batch
    When: Attempting to delete documents
    Then: Should handle validation error appropriately
    """
    invalid_docs = [{"id": "not-a-uuid"}, {"wrong_field": "value"}, None]

    result = delete_operation.execute_batch(invalid_docs)

    assert result.success is False
    assert result.error_count == len(invalid_docs)
    assert len(result.failed_items) == len(invalid_docs)
    assert all("error" in item for item in result.failed_items)
