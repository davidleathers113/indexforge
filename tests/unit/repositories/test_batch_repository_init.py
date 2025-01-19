"""Test batch repository initialization.

This module contains tests for initializing batch repositories with various configurations.
"""

from unittest.mock import Mock, patch

import pytest
import weaviate

from src.api.repositories.weaviate.batch import BatchRepository
from src.api.repositories.weaviate.exceptions import BatchConfigurationError

# Test configuration
TEST_CONFIG = {
    "url": "http://localhost:8080",
    "auth_credentials": weaviate.auth.AuthApiKey(api_key="test-api-key"),
    "collection_name": "test_collection",
    "batch_size": 100,
    "dynamic": True,
    "creation_time_ms": 100,
}


@pytest.fixture
def mock_client():
    """Setup mock Weaviate client."""
    with patch("weaviate.Client") as mock_client:
        client = mock_client.return_value
        client.collections.get.return_value = Mock()
        yield client


@pytest.fixture
def mock_collection():
    """Setup mock Weaviate collection."""
    collection = Mock()
    collection.batch.configure.return_value = None
    return collection


def test_repository_initialization_with_valid_config(mock_client):
    """
    Test repository initialization with valid configuration.

    Given: Valid configuration parameters
    When: Initializing the BatchRepository
    Then: Repository should be properly initialized with the given configuration
    """
    repo = BatchRepository(
        client=mock_client,
        collection_name=TEST_CONFIG["collection_name"],
        batch_size=TEST_CONFIG["batch_size"],
        dynamic=TEST_CONFIG["dynamic"],
        creation_time_ms=TEST_CONFIG["creation_time_ms"],
    )

    assert repo._collection_name == TEST_CONFIG["collection_name"]
    assert repo.batch_config.batch_size == TEST_CONFIG["batch_size"]
    assert repo.batch_config.dynamic is TEST_CONFIG["dynamic"]
    assert repo.batch_config.creation_time == TEST_CONFIG["creation_time_ms"]


def test_repository_initialization_with_defaults(mock_client):
    """
    Test repository initialization with default values.

    Given: Minimal required configuration
    When: Initializing the BatchRepository
    Then: Repository should use default values for optional parameters
    """
    repo = BatchRepository(client=mock_client, collection_name=TEST_CONFIG["collection_name"])

    assert repo._collection_name == TEST_CONFIG["collection_name"]
    assert repo.batch_config.batch_size > 0  # Should have a default batch size
    assert repo.batch_config.dynamic is True  # Should default to True
    assert repo.batch_config.creation_time > 0  # Should have a default creation time


def test_repository_initialization_validates_batch_size(mock_client):
    """
    Test batch size validation during initialization.

    Given: Invalid batch size configurations
    When: Initializing the BatchRepository
    Then: Appropriate validation errors should be raised
    """
    invalid_batch_sizes = [0, -1, "not-a-number"]

    for batch_size in invalid_batch_sizes:
        with pytest.raises(BatchConfigurationError, match="Invalid batch size"):
            BatchRepository(
                client=mock_client,
                collection_name=TEST_CONFIG["collection_name"],
                batch_size=batch_size,
            )


def test_repository_initialization_validates_creation_time(mock_client):
    """
    Test creation time validation during initialization.

    Given: Invalid creation time configurations
    When: Initializing the BatchRepository
    Then: Appropriate validation errors should be raised
    """
    invalid_creation_times = [0, -1, "not-a-number"]

    for creation_time in invalid_creation_times:
        with pytest.raises(BatchConfigurationError, match="Invalid creation time"):
            BatchRepository(
                client=mock_client,
                collection_name=TEST_CONFIG["collection_name"],
                creation_time_ms=creation_time,
            )
