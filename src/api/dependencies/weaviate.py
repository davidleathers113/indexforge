"""Weaviate client dependency."""

from functools import lru_cache
from urllib.parse import urlparse

import weaviate
from weaviate.auth import AuthApiKey
from weaviate.config import AdditionalConfig, Proxies
from weaviate.exceptions import WeaviateConnectionError

from src.api.config.settings import get_settings
from src.api.errors.weaviate_error_handling import with_weaviate_error_handling


settings = get_settings()


def create_additional_config() -> AdditionalConfig:
    """Create additional configuration for Weaviate client.

    Returns:
        AdditionalConfig: Configuration instance with timeout and batch settings.
    """
    return AdditionalConfig(
        timeout_config=weaviate.config.TimeoutConfig(
            timeout=settings.WEAVIATE_TIMEOUT,
            connection_timeout=settings.WEAVIATE_CONNECTION_TIMEOUT,
            retries=settings.WEAVIATE_TIMEOUT_RETRIES,
        ),
        headers={
            "X-Request-ID": "document-api",
            "User-Agent": "IndexForge/1.0",
        },
        proxies=(
            Proxies(
                http=settings.HTTP_PROXY,
                https=settings.HTTPS_PROXY,
            )
            if settings.HTTP_PROXY or settings.HTTPS_PROXY
            else None
        ),
        trust_env=True,
        grpc_port=settings.WEAVIATE_GRPC_PORT if settings.WEAVIATE_ENABLE_GRPC else None,
    )


def create_embedded_client(
    url: str,
    additional_config: AdditionalConfig,
    auth: AuthApiKey | None = None,
) -> weaviate.WeaviateClient:
    """Create a Weaviate client for embedded/local instance.

    Args:
        url: The Weaviate URL.
        additional_config: Additional configuration options.
        auth: Optional authentication credentials.

    Returns:
        WeaviateClient: Configured client for local instance.

    Raises:
        WeaviateConnectionError: If connection fails or configuration is invalid.
    """
    try:
        return weaviate.Client(
            url=url,
            port=settings.WEAVIATE_PORT,
            additional_config=additional_config,
            auth_client_secret=auth,
        )
    except Exception as e:
        raise WeaviateConnectionError(
            f"Failed to connect to embedded Weaviate instance: {e!s}"
        ) from e


def create_custom_client(
    url: str,
    additional_config: AdditionalConfig,
    auth: AuthApiKey | None = None,
) -> weaviate.WeaviateClient:
    """Create a Weaviate client for custom/remote instance.

    Args:
        url: The Weaviate URL.
        additional_config: Additional configuration options.
        auth: Optional authentication credentials.

    Returns:
        WeaviateClient: Configured client for remote instance.

    Raises:
        WeaviateConnectionError: If connection fails or configuration is invalid.
    """
    try:
        return weaviate.Client(
            url=url,
            additional_config=additional_config,
            auth_client_secret=auth,
        )
    except Exception as e:
        raise WeaviateConnectionError(f"Failed to connect to Weaviate at {url}: {e!s}") from e


@lru_cache
@with_weaviate_error_handling
def get_weaviate_client() -> weaviate.WeaviateClient:
    """Get a configured Weaviate client.

    Returns:
        WeaviateClient: A configured Weaviate client instance.

    Raises:
        WeaviateConnectionError: If client creation or connection fails.
    """
    url = urlparse(settings.WEAVIATE_URL)
    additional_config = create_additional_config()
    auth = AuthApiKey(api_key=settings.WEAVIATE_API_KEY) if settings.WEAVIATE_API_KEY else None

    # Use connect_to_embedded for local development or connect_to_custom for production
    if url.hostname in ("localhost", "127.0.0.1"):
        client = create_embedded_client(settings.WEAVIATE_URL, additional_config, auth)
    else:
        client = create_custom_client(settings.WEAVIATE_URL, additional_config, auth)

    return client
