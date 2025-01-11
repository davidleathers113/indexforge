"""Weaviate client dependency."""

from functools import lru_cache

import weaviate

from src.api.config.settings import settings


@lru_cache()
def get_weaviate_client() -> weaviate.Client:
    """Get or create Weaviate client instance.

    Returns:
        weaviate.Client: Configured Weaviate client
    """
    auth_config = (
        weaviate.auth.AuthApiKey(api_key=settings.WEAVIATE_API_KEY)
        if settings.WEAVIATE_API_KEY
        else None
    )

    return weaviate.Client(
        url=settings.WEAVIATE_URL,
        auth_client_secret=auth_config,
        additional_headers={"X-Request-ID": "document-api"},
    )
