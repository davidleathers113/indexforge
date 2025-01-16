"""Test batch deletion functionality of DeleteOperation."""

from unittest.mock import Mock

import pytest

from src.api.repositories.weaviate.operations.delete import DeleteOperation


# Test data constants
TEST_BATCH = [
    {"id": "550e8400-e29b-41d4-a716-446655440000"},
    {"id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8"},
    {"id": "7ba7b810-9dad-11d1-80b4-00c04fd430c8"},
]


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


def test_delete_batch_success(delete_operation, mock_collection):
    """
    Test successful batch deletion.

    Given: A batch of valid document IDs
    When: Executing the batch deletion
    Then: All documents should be deleted successfully
    """
    result = delete_operation.execute_batch(TEST_BATCH)

    assert result.success is True
    assert result.processed_count == len(TEST_BATCH)
    assert result.error_count == 0
    assert len(result.successful_items) == len(TEST_BATCH)
    assert not result.failed_items


def test_delete_batch_partial_failure(delete_operation, mock_collection):
    """
    Test batch deletion with partial failures.

    Given: A batch where some deletions fail
    When: Executing the batch deletion
    Then: Failures should be handled and reported correctly
    """
    # Setup mock to fail for second document
    mock_collection.batch.delete_objects.side_effect = [
        {"status": "SUCCESS"},
        {"status": "FAILED", "error": "Document not found"},
        {"status": "SUCCESS"},
    ]

    result = delete_operation.execute_batch(TEST_BATCH)

    assert result.success is False
    assert result.processed_count == len(TEST_BATCH)
    assert result.error_count == 1
    assert len(result.successful_items) == 2
    assert len(result.failed_items) == 1
    assert "Document not found" in str(result.failed_items[0]["error"])


def test_delete_batch_complete_failure(delete_operation, mock_collection):
    """
    Test batch deletion with complete failure.

    Given: A batch where all deletions fail
    When: Executing the batch deletion
    Then: Complete failure should be handled appropriately
    """
    mock_collection.batch.delete_objects.side_effect = Exception("Deletion failed")

    result = delete_operation.execute_batch(TEST_BATCH)

    assert result.success is False
    assert result.processed_count == 0
    assert result.error_count == len(TEST_BATCH)
    assert not result.successful_items
    assert len(result.failed_items) == len(TEST_BATCH)


def test_delete_empty_batch(delete_operation):
    """
    Test deletion of empty batch.

    Given: An empty batch
    When: Executing the batch deletion
    Then: Should handle empty batch appropriately
    """
    result = delete_operation.execute_batch([])

    assert result.success is True
    assert result.processed_count == 0
    assert result.error_count == 0
    assert not result.successful_items
    assert not result.failed_items


def test_delete_batch_with_retries(delete_operation, mock_collection):
    """
    Test batch deletion with retries.

    Given: A batch where deletion initially fails but succeeds on retry
    When: Executing the batch deletion
    Then: Should retry failed operations and succeed
    """
    # Mock to fail first attempt but succeed on retry
    mock_collection.batch.delete_objects.side_effect = [
        Exception("First attempt"),
        {"status": "SUCCESS"},
        {"status": "SUCCESS"},
        {"status": "SUCCESS"},
    ]

    result = delete_operation.execute_batch(TEST_BATCH)

    assert result.success is True
    assert result.processed_count == len(TEST_BATCH)
    assert result.error_count == 0
    assert len(result.successful_items) == len(TEST_BATCH)
    assert not result.failed_items
