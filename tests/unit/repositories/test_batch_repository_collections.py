"""Test collection handling functionality of BatchRepository."""

from unittest.mock import Mock

import pytest

from src.api.repositories.weaviate.exceptions import CollectionError
from src.api.repositories.weaviate.repository import BatchRepository


# Test data constants
TEST_CONFIG = {
    "url": "http://localhost:8080",
    "api_key": "test-api-key",
    "timeout": 300,
    "batch_size": 100,
}


@pytest.fixture
def mock_client():
    """Setup mock Weaviate client."""
    client = Mock()
    client.collections.create.return_value = Mock()
    return client


@pytest.fixture
def mock_collection():
    """Setup mock Weaviate collection."""
    collection = Mock()
    collection.batch.configure.return_value = None
    return collection


@pytest.fixture
def repository(mock_client):
    """Setup BatchRepository instance with mocked client."""
    return BatchRepository(client=mock_client, **TEST_CONFIG)


def test_get_collection_success(repository, mock_client, mock_collection):
    """
    Test successful collection retrieval.

    Given: A valid collection name
    When: Requesting the collection
    Then: Collection should be retrieved successfully
    """
    mock_client.collections.get.return_value = mock_collection
    collection_name = "test_collection"

    result = repository.get_collection(collection_name)

    assert result == mock_collection
    mock_client.collections.get.assert_called_once_with(collection_name)


def test_get_collection_not_found(repository, mock_client):
    """
    Test collection not found scenario.

    Given: A non-existent collection name
    When: Requesting the collection
    Then: Appropriate error should be raised
    """
    mock_client.collections.get.side_effect = Exception("Collection not found")
    collection_name = "non_existent"

    with pytest.raises(CollectionError, match="Collection not found"):
        repository.get_collection(collection_name)


def test_create_collection_success(repository, mock_client, mock_collection):
    """
    Test successful collection creation.

    Given: Valid collection configuration
    When: Creating a new collection
    Then: Collection should be created successfully
    """
    mock_client.collections.create.return_value = mock_collection
    collection_config = {
        "name": "test_collection",
        "properties": [
            {"name": "text", "dataType": ["text"]},
            {"name": "metadata", "dataType": ["object"]},
        ],
    }

    result = repository.create_collection(collection_config)

    assert result == mock_collection
    mock_client.collections.create.assert_called_once_with(collection_config)


def test_create_collection_already_exists(repository, mock_client):
    """
    Test collection creation when collection already exists.

    Given: A collection configuration for an existing collection
    When: Attempting to create the collection
    Then: Appropriate error should be raised
    """
    mock_client.collections.create.side_effect = Exception("Collection already exists")
    collection_config = {"name": "existing_collection"}

    with pytest.raises(CollectionError, match="Collection already exists"):
        repository.create_collection(collection_config)


def test_configure_collection_batch_settings(repository, mock_client, mock_collection):
    """
    Test configuration of collection batch settings.

    Given: Valid batch configuration settings
    When: Configuring collection batch settings
    Then: Settings should be applied successfully
    """
    mock_client.collections.get.return_value = mock_collection
    collection_name = "test_collection"
    batch_config = {"batch_size": 100, "dynamic": True, "timeout_retries": 3}

    repository.configure_collection_batch(collection_name, batch_config)

    mock_collection.batch.configure.assert_called_once_with(**batch_config)
