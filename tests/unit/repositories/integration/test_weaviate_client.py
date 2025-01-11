"""Test Weaviate client initialization and integration functionality.

This module contains integration tests for the Weaviate client initialization,
focusing on connection handling, authentication, and timeout configurations.
"""

from unittest.mock import Mock, patch

import pytest
from requests.exceptions import ConnectionError, Timeout

from src.api.repositories.weaviate.client import WeaviateClient
from src.api.repositories.weaviate.exceptions import (
    AuthenticationError,
    ClientInitializationError,
    TimeoutConfigurationError,
)

# Test data constants
TEST_CONFIG = {
    "url": "http://localhost:8080",
    "api_key": "test-api-key",
    "timeout": 300,
    "retry_count": 3,
}


@pytest.fixture
def mock_weaviate():
    """Setup mock Weaviate client."""
    with patch("weaviate.Client") as mock_client:
        yield mock_client


@pytest.fixture
def client_factory():
    """Create a function to instantiate WeaviateClient with custom config."""

    def create_client(**kwargs):
        config = {**TEST_CONFIG, **kwargs}
        return WeaviateClient(**config)

    return create_client


def test_successful_client_initialization(mock_weaviate, client_factory):
    """
    Test successful client initialization.

    Given: Valid configuration parameters
    When: Initializing the Weaviate client
    Then: Client should be initialized successfully with correct configuration
    """
    client = client_factory()

    assert client.url == TEST_CONFIG["url"]
    assert client.api_key == TEST_CONFIG["api_key"]
    assert client.timeout == TEST_CONFIG["timeout"]
    mock_weaviate.assert_called_once()


def test_connection_failure_handling(mock_weaviate, client_factory):
    """
    Test handling of connection failures during initialization.

    Given: A network connectivity issue
    When: Attempting to initialize the client
    Then: Should raise appropriate connection error with retry information
    """
    mock_weaviate.side_effect = ConnectionError("Failed to connect")

    with pytest.raises(ClientInitializationError) as exc_info:
        client_factory()

    assert "Failed to connect" in str(exc_info.value)
    assert "after 3 retries" in str(exc_info.value)


def test_authentication_validation(mock_weaviate, client_factory):
    """
    Test authentication validation during initialization.

    Given: Invalid API key configuration
    When: Attempting to initialize the client
    Then: Should raise authentication error
    """
    mock_weaviate.side_effect = Exception("Invalid API key")

    with pytest.raises(AuthenticationError) as exc_info:
        client_factory(api_key="invalid-key")

    assert "Invalid API key" in str(exc_info.value)


def test_timeout_configuration(mock_weaviate, client_factory):
    """
    Test timeout configuration validation.

    Given: Various timeout configurations
    When: Initializing the client with these configurations
    Then: Should validate and apply timeout settings correctly
    """
    # Test valid timeout
    client = client_factory(timeout=600)
    assert client.timeout == 600

    # Test invalid timeout
    with pytest.raises(TimeoutConfigurationError):
        client_factory(timeout=-1)


def test_retry_mechanism(mock_weaviate, client_factory):
    """
    Test retry mechanism during initialization.

    Given: Temporary connection issues that resolve after retries
    When: Initializing the client
    Then: Should successfully connect after retrying
    """
    # Mock connection failure on first two attempts, success on third
    mock_weaviate.side_effect = [
        ConnectionError("First attempt"),
        ConnectionError("Second attempt"),
        Mock(),  # Success on third attempt
    ]

    client = client_factory()
    assert client is not None
    assert mock_weaviate.call_count == 3


def test_connection_timeout_handling(mock_weaviate, client_factory):
    """
    Test handling of connection timeouts.

    Given: Connection attempts that timeout
    When: Initializing the client
    Then: Should handle timeouts appropriately with retry mechanism
    """
    mock_weaviate.side_effect = Timeout("Connection timed out")

    with pytest.raises(ClientInitializationError) as exc_info:
        client_factory()

    assert "Connection timed out" in str(exc_info.value)
    assert mock_weaviate.call_count == TEST_CONFIG["retry_count"]
