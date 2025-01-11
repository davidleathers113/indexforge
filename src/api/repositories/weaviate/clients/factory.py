"""Weaviate client factory."""

from functools import lru_cache
from typing import Optional
from urllib.parse import urlparse

import weaviate.classes as wvc
from weaviate.auth import AuthApiKey
from weaviate.config import AdditionalConfig, Headers, Proxies
from weaviate.exceptions import WeaviateConnectionError

from src.api.config.settings import settings


class WeaviateClientFactory:
    """Factory for creating Weaviate clients."""

    @staticmethod
    def create_additional_config() -> AdditionalConfig:
        """Create additional configuration for Weaviate client.

        Returns:
            AdditionalConfig: Configuration instance with timeout and batch settings.
        """
        return AdditionalConfig(
            timeout=settings.WEAVIATE_TIMEOUT,
            batch_size=settings.WEAVIATE_BATCH_SIZE,
            timeout_retries=settings.WEAVIATE_TIMEOUT_RETRIES,
            connection_timeout=settings.WEAVIATE_CONNECTION_TIMEOUT,
            headers=Headers(
                {
                    "X-Request-ID": "document-api",
                    "User-Agent": "IndexForge/1.0",
                }
            ),
            proxies=(
                Proxies(
                    http=settings.HTTP_PROXY,
                    https=settings.HTTPS_PROXY,
                )
                if settings.HTTP_PROXY or settings.HTTPS_PROXY
                else None
            ),
            trust_env=True,
            grpc_secure=settings.WEAVIATE_ENABLE_GRPC,
        )

    @classmethod
    def create_auth_config(cls) -> Optional[AuthApiKey]:
        """Create authentication configuration.

        Returns:
            Optional[AuthApiKey]: Authentication configuration if API key is set
        """
        return AuthApiKey(api_key=settings.WEAVIATE_API_KEY) if settings.WEAVIATE_API_KEY else None

    @classmethod
    def create_embedded_client(cls) -> wvc.WeaviateClient:
        """Create client for embedded Weaviate instance.

        Returns:
            WeaviateClient: Configured client for embedded instance

        Raises:
            WeaviateConnectionError: If connection fails
        """
        try:
            return wvc.connect_to_embedded(
                port=settings.WEAVIATE_PORT,
                grpc_port=settings.WEAVIATE_GRPC_PORT,
                auth_credentials=cls.create_auth_config(),
                additional_config=cls.create_additional_config(),
            )
        except Exception as e:
            raise WeaviateConnectionError(f"Failed to connect to embedded instance: {str(e)}")

    @classmethod
    def create_custom_client(cls) -> wvc.WeaviateClient:
        """Create client for custom Weaviate instance.

        Returns:
            WeaviateClient: Configured client for custom instance

        Raises:
            WeaviateConnectionError: If connection fails
        """
        try:
            url = urlparse(settings.WEAVIATE_URL)
            return wvc.connect_to_custom(
                host=url.hostname,
                port=url.port or settings.WEAVIATE_PORT,
                grpc_port=settings.WEAVIATE_GRPC_PORT,
                secure=url.scheme == "https",
                auth_credentials=cls.create_auth_config(),
                additional_config=cls.create_additional_config(),
            )
        except Exception as e:
            raise WeaviateConnectionError(f"Failed to connect to custom instance: {str(e)}")


@lru_cache()
def get_weaviate_client() -> wvc.WeaviateClient:
    """Get or create Weaviate client instance.

    Returns:
        WeaviateClient: Configured Weaviate client

    Raises:
        WeaviateConnectionError: If connection fails
    """
    url = urlparse(settings.WEAVIATE_URL)

    try:
        # Use embedded client for localhost/127.0.0.1
        if url.hostname in ("localhost", "127.0.0.1"):
            return WeaviateClientFactory.create_embedded_client()

        # Use custom client for remote instances
        return WeaviateClientFactory.create_custom_client()
    except WeaviateConnectionError:
        raise
    except Exception as e:
        raise WeaviateConnectionError(f"Failed to create Weaviate client: {str(e)}")
