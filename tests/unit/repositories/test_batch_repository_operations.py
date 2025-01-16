"""Test document operations functionality of BatchRepository."""

from unittest.mock import Mock

import pytest

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
    {"id": "3", "text": "Third document", "metadata": {"source": "test"}},
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


def test_index_documents_success(repository, mock_collection):
    """
    Test successful document indexing.

    Given: A batch of valid documents
    When: Indexing the documents
    Then: All documents should be indexed successfully
    """
    collection_name = "test_collection"

    result = repository.index_documents(collection_name, TEST_DOCUMENTS)

    assert result.success is True
    assert result.processed_count == len(TEST_DOCUMENTS)
    assert result.error_count == 0
    mock_collection.batch.add_objects.assert_called_once()


def test_index_documents_partial_failure(repository, mock_collection):
    """
    Test document indexing with partial failures.

    Given: A batch where some documents fail indexing
    When: Indexing the documents
    Then: Failures should be handled and reported correctly
    """
    mock_collection.batch.add_objects.side_effect = [
        {"status": "SUCCESS"},
        {"status": "FAILED", "error": "Validation error"},
        {"status": "SUCCESS"},
    ]
    collection_name = "test_collection"

    result = repository.index_documents(collection_name, TEST_DOCUMENTS)

    assert result.success is False
    assert result.error_count > 0
    assert len(result.failed_items) > 0


def test_delete_documents_success(repository, mock_collection):
    """
    Test successful document deletion.

    Given: A batch of valid document IDs
    When: Deleting the documents
    Then: All documents should be deleted successfully
    """
    collection_name = "test_collection"
    document_ids = [doc["id"] for doc in TEST_DOCUMENTS]

    result = repository.delete_documents(collection_name, document_ids)

    assert result.success is True
    assert result.processed_count == len(document_ids)
    assert result.error_count == 0
    mock_collection.batch.delete_objects.assert_called_once()


def test_delete_documents_partial_failure(repository, mock_collection):
    """
    Test document deletion with partial failures.

    Given: A batch where some deletions fail
    When: Deleting the documents
    Then: Failures should be handled and reported correctly
    """
    mock_collection.batch.delete_objects.side_effect = [
        {"status": "SUCCESS"},
        {"status": "FAILED", "error": "Document not found"},
        {"status": "SUCCESS"},
    ]
    collection_name = "test_collection"
    document_ids = [doc["id"] for doc in TEST_DOCUMENTS]

    result = repository.delete_documents(collection_name, document_ids)

    assert result.success is False
    assert result.error_count > 0
    assert len(result.failed_items) > 0


def test_handle_empty_batch(repository):
    """
    Test handling of empty batches.

    Given: Empty document batches
    When: Attempting operations with empty batches
    Then: Should handle empty batches appropriately
    """
    collection_name = "test_collection"

    index_result = repository.index_documents(collection_name, [])
    assert index_result.success is True
    assert index_result.processed_count == 0

    delete_result = repository.delete_documents(collection_name, [])
    assert delete_result.success is True
    assert delete_result.processed_count == 0
