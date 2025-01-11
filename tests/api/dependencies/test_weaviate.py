"""Tests for Weaviate client dependency."""

from unittest.mock import MagicMock, patch

import pytest
from weaviate.auth import AuthApiKey
from weaviate.config import AdditionalConfig
from weaviate.exceptions import WeaviateConnectionError

from src.api.dependencies.weaviate import (
    create_additional_config,
    create_custom_client,
    create_embedded_client,
    get_weaviate_client,
)


@pytest.fixture
def mock_settings():
    """Mock settings for tests."""
    with patch("src.api.dependencies.weaviate.settings") as mock_settings:
        mock_settings.WEAVIATE_URL = "http://localhost:8080"
        mock_settings.WEAVIATE_API_KEY = "test-api-key"
        mock_settings.WEAVIATE_PORT = 8080
        mock_settings.WEAVIATE_GRPC_PORT = 50051
        mock_settings.WEAVIATE_TIMEOUT = 30
        mock_settings.WEAVIATE_CONNECTION_TIMEOUT = 10
        mock_settings.WEAVIATE_BATCH_SIZE = 100
        mock_settings.WEAVIATE_TIMEOUT_RETRIES = 3
        mock_settings.WEAVIATE_ENABLE_GRPC = True
        mock_settings.HTTP_PROXY = None
        mock_settings.HTTPS_PROXY = None
        yield mock_settings


def test_create_additional_config(mock_settings):
    """Test creation of additional configuration."""
    config = create_additional_config()
    assert isinstance(config, AdditionalConfig)
    assert config.timeout == mock_settings.WEAVIATE_TIMEOUT
    assert config.batch_size == mock_settings.WEAVIATE_BATCH_SIZE
    assert config.timeout_retries == mock_settings.WEAVIATE_TIMEOUT_RETRIES
    assert config.grpc_secure == mock_settings.WEAVIATE_ENABLE_GRPC
    assert "X-Request-ID" in config.headers
    assert "User-Agent" in config.headers
    assert config.proxies is None


@pytest.mark.asyncio
async def test_create_embedded_client_success(mock_settings):
    """Test successful creation of embedded client."""
    with patch("weaviate.classes.init.connect_to_embedded") as mock_connect:
        mock_client = MagicMock()
        mock_connect.return_value = mock_client

        config = create_additional_config()
        auth = AuthApiKey(api_key=mock_settings.WEAVIATE_API_KEY)
        client = create_embedded_client(mock_settings.WEAVIATE_URL, config, auth)

        assert client == mock_client
        mock_connect.assert_called_once_with(
            port=mock_settings.WEAVIATE_PORT,
            grpc_port=mock_settings.WEAVIATE_GRPC_PORT,
            additional_config=config,
            auth_credentials=auth,
        )


@pytest.mark.asyncio
async def test_create_embedded_client_failure(mock_settings):
    """Test failure handling in embedded client creation."""
    with patch("weaviate.classes.init.connect_to_embedded") as mock_connect:
        mock_connect.side_effect = Exception("Connection failed")
        config = create_additional_config()
        auth = AuthApiKey(api_key=mock_settings.WEAVIATE_API_KEY)

        with pytest.raises(WeaviateConnectionError) as exc_info:
            create_embedded_client(mock_settings.WEAVIATE_URL, config, auth)

        assert "Failed to connect to embedded Weaviate instance" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_custom_client_success(mock_settings):
    """Test successful creation of custom client."""
    with patch("weaviate.classes.init.connect_to_custom") as mock_connect:
        mock_client = MagicMock()
        mock_connect.return_value = mock_client

        config = create_additional_config()
        auth = AuthApiKey(api_key=mock_settings.WEAVIATE_API_KEY)
        client = create_custom_client(mock_settings.WEAVIATE_URL, config, auth)

        assert client == mock_client
        mock_connect.assert_called_once_with(
            url=mock_settings.WEAVIATE_URL,
            additional_config=config,
            auth_credentials=auth,
        )


@pytest.mark.asyncio
async def test_create_custom_client_failure(mock_settings):
    """Test failure handling in custom client creation."""
    with patch("weaviate.classes.init.connect_to_custom") as mock_connect:
        mock_connect.side_effect = Exception("Connection failed")
        config = create_additional_config()
        auth = AuthApiKey(api_key=mock_settings.WEAVIATE_API_KEY)

        with pytest.raises(WeaviateConnectionError) as exc_info:
            create_custom_client(mock_settings.WEAVIATE_URL, config, auth)

        assert "Failed to connect to Weaviate at" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_weaviate_client_local(mock_settings):
    """Test getting Weaviate client for local instance."""
    with patch("src.api.dependencies.weaviate.create_embedded_client") as mock_embedded:
        mock_client = MagicMock()
        mock_embedded.return_value = mock_client

        client = get_weaviate_client()
        assert client == mock_client
        mock_embedded.assert_called_once()


@pytest.mark.asyncio
async def test_get_weaviate_client_remote(mock_settings):
    """Test getting Weaviate client for remote instance."""
    mock_settings.WEAVIATE_URL = "https://remote-weaviate:8080"

    with patch("src.api.dependencies.weaviate.create_custom_client") as mock_custom:
        mock_client = MagicMock()
        mock_custom.return_value = mock_client

        client = get_weaviate_client()
        assert client == mock_client
        mock_custom.assert_called_once()
