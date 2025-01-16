"""Test initialization and configuration of BatchRepository."""

from unittest.mock import Mock

import pytest

from src.api.repositories.weaviate.exceptions import RepositoryConfigError
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


def test_repository_initialization_with_valid_config(mock_client):
    """
    Test repository initialization with valid configuration.

    Given: Valid configuration parameters
    When: Initializing the BatchRepository
    Then: Repository should be properly initialized with the given configuration
    """
    repo = BatchRepository(client=mock_client, **TEST_CONFIG)

    assert repo.url == TEST_CONFIG["url"]
    assert repo.api_key == TEST_CONFIG["api_key"]
    assert repo.timeout == TEST_CONFIG["timeout"]
    assert repo.batch_size == TEST_CONFIG["batch_size"]


def test_repository_initialization_with_defaults(mock_client):
    """
    Test repository initialization with default values.

    Given: Minimal required configuration
    When: Initializing the BatchRepository
    Then: Repository should use default values for optional parameters
    """
    minimal_config = {"url": TEST_CONFIG["url"]}
    repo = BatchRepository(client=mock_client, **minimal_config)

    assert repo.url == minimal_config["url"]
    assert repo.api_key is None
    assert repo.timeout > 0  # Should have a default timeout
    assert repo.batch_size > 0  # Should have a default batch size


def test_repository_initialization_validates_url(mock_client):
    """
    Test URL validation during initialization.

    Given: Invalid URL configurations
    When: Initializing the BatchRepository
    Then: Appropriate validation errors should be raised
    """
    invalid_configs = [{"url": ""}, {"url": "not-a-url"}, {"url": "ftp://invalid-scheme.com"}]

    for config in invalid_configs:
        with pytest.raises(RepositoryConfigError, match="Invalid URL"):
            BatchRepository(client=mock_client, **config)


def test_repository_initialization_validates_batch_size(mock_client):
    """
    Test batch size validation during initialization.

    Given: Invalid batch size configurations
    When: Initializing the BatchRepository
    Then: Appropriate validation errors should be raised
    """
    invalid_configs = [
        {**TEST_CONFIG, "batch_size": 0},
        {**TEST_CONFIG, "batch_size": -1},
        {**TEST_CONFIG, "batch_size": "not-a-number"},
    ]

    for config in invalid_configs:
        with pytest.raises(RepositoryConfigError, match="Invalid batch size"):
            BatchRepository(client=mock_client, **config)


def test_repository_initialization_validates_timeout(mock_client):
    """
    Test timeout validation during initialization.

    Given: Invalid timeout configurations
    When: Initializing the BatchRepository
    Then: Appropriate validation errors should be raised
    """
    invalid_configs = [
        {**TEST_CONFIG, "timeout": 0},
        {**TEST_CONFIG, "timeout": -1},
        {**TEST_CONFIG, "timeout": "not-a-number"},
    ]

    for config in invalid_configs:
        with pytest.raises(RepositoryConfigError, match="Invalid timeout"):
            BatchRepository(client=mock_client, **config)
