"""Base Weaviate repository."""

from typing import Optional

import weaviate.classes as wvc
from weaviate.classes.query import Filter
from weaviate.types import Include

from src.api.errors.weaviate_error_handling import with_weaviate_error_handling


class BaseWeaviateRepository:
    """Base class for Weaviate repositories."""

    def __init__(self, client: wvc.WeaviateClient, collection: str):
        """Initialize repository.

        Args:
            client: Weaviate client instance
            collection: Collection name to operate on
        """
        self.client = client
        self.collection = collection

    @property
    def collection_ref(self) -> wvc.Collection:
        """Get collection reference.

        Returns:
            Collection reference for operations
        """
        return self.client.collections.get(self.collection)

    def _build_filter(self, filters: list[Filter]) -> Optional[Filter]:
        """Build filter from list of conditions.

        Args:
            filters: List of filter conditions

        Returns:
            Combined filter or None if no filters
        """
        return Filter.and_(filters) if filters else None

    def _get_include_properties(self, include_vector: bool = False) -> Include:
        """Get properties to include in response.

        Args:
            include_vector: Whether to include vector in response

        Returns:
            Include configuration
        """
        properties = Include.ALL
        if include_vector:
            properties = Include.ALL | Include.VECTOR
        return properties

    @with_weaviate_error_handling
    async def health_check(self) -> bool:
        """Check if repository is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            self.client.collections.list()
            return True
        except Exception:
            return False
