"""Test batch processing functionality of IndexOperation."""

from unittest.mock import Mock

import pytest

from src.api.repositories.weaviate.operations.index import IndexOperation


# Test data constants
TEST_BATCH = [
    {"id": "1", "text": "First document", "metadata": {"source": "test"}},
    {"id": "2", "text": "Second document", "metadata": {"source": "test"}},
    {"id": "3", "text": "Third document", "metadata": {"source": "test"}},
]


@pytest.fixture
def mock_collection():
    """Setup mock Weaviate collection."""
    collection = Mock()
    collection.batch.add_object.return_value = {"status": "SUCCESS"}
    return collection


@pytest.fixture
def index_operation(mock_collection):
    """Setup IndexOperation instance with mocked dependencies."""
    vector_service = Mock()
    vector_service.encode.return_value = [[0.1, 0.2, 0.3]]
    return IndexOperation(vector_service=vector_service, collection=mock_collection)


def test_process_batch_success(index_operation, mock_collection):
    """
    Test successful batch processing.

    Given: A batch of valid documents
    When: Processing the batch
    Then: All documents should be processed successfully
    """
    result = index_operation.execute_batch(TEST_BATCH)

    assert result.success is True
    assert result.processed_count == len(TEST_BATCH)
    assert result.error_count == 0
    assert len(result.successful_items) == len(TEST_BATCH)
    assert not result.failed_items


def test_process_batch_partial_failure(index_operation, mock_collection):
    """
    Test batch processing with partial failures.

    Given: A batch where some documents fail processing
    When: Processing the batch
    Then: Failures should be handled and reported correctly
    """
    # Setup mock to fail for second document
    mock_collection.batch.add_object.side_effect = [
        {"status": "SUCCESS"},
        {"status": "FAILED", "error": "Test error"},
        {"status": "SUCCESS"},
    ]

    result = index_operation.execute_batch(TEST_BATCH)

    assert result.success is False
    assert result.processed_count == len(TEST_BATCH)
    assert result.error_count == 1
    assert len(result.successful_items) == 2
    assert len(result.failed_items) == 1
    assert result.failed_items[0]["error"] == "Test error"


def test_process_batch_complete_failure(index_operation, mock_collection):
    """
    Test batch processing with complete failure.

    Given: A batch where all documents fail processing
    When: Processing the batch
    Then: Complete failure should be handled appropriately
    """
    mock_collection.batch.add_object.side_effect = Exception("Batch processing failed")

    result = index_operation.execute_batch(TEST_BATCH)

    assert result.success is False
    assert result.processed_count == 0
    assert result.error_count == len(TEST_BATCH)
    assert not result.successful_items
    assert len(result.failed_items) == len(TEST_BATCH)


def test_process_empty_batch(index_operation):
    """
    Test processing of empty batch.

    Given: An empty batch
    When: Processing the batch
    Then: Should handle empty batch appropriately
    """
    result = index_operation.execute_batch([])

    assert result.success is True
    assert result.processed_count == 0
    assert result.error_count == 0
    assert not result.successful_items
    assert not result.failed_items


def test_process_batch_with_retries(index_operation, mock_collection):
    """
    Test batch processing with retries.

    Given: A batch where processing initially fails but succeeds on retry
    When: Processing the batch
    Then: Should retry failed operations and succeed
    """
    # Mock to fail first attempt but succeed on retry
    mock_collection.batch.add_object.side_effect = [
        Exception("First attempt"),
        {"status": "SUCCESS"},
        {"status": "SUCCESS"},
        {"status": "SUCCESS"},
    ]

    result = index_operation.execute_batch(TEST_BATCH)

    assert result.success is True
    assert result.processed_count == len(TEST_BATCH)
    assert result.error_count == 0
    assert len(result.successful_items) == len(TEST_BATCH)
    assert not result.failed_items
