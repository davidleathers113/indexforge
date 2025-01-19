"""Base Weaviate repository implementation.

This module provides the base repository class for interacting with Weaviate,
implementing common functionality and defining the interface for specialized repositories.
"""

import logging
from typing import Any

import weaviate
from weaviate.collections import Collection
from weaviate.collections.classes.filters import Filter

from src.api.errors.weaviate_error_handling import with_weaviate_error_handling

logger = logging.getLogger(__name__)


class BaseWeaviateRepository:
    """Base class for Weaviate repositories."""

    def __init__(self, client: weaviate.Client, collection_name: str):
        """Initialize the base repository.

        Args:
            client: Weaviate client instance
            collection_name: Name of the collection to operate on
        """
        logger.debug("Initializing BaseWeaviateRepository with collection: %s", collection_name)
        self._client = client
        self._collection_name = collection_name
        self._collection: Collection | None = None

    @property
    def collection_ref(self) -> Collection:
        """Get the collection reference, initializing it if needed.

        Returns:
            Collection: Reference to the Weaviate collection
        """
        if self._collection is None:
            logger.debug("Initializing collection reference for: %s", self._collection_name)
            self._collection = self._client.collections.get(self._collection_name)
        return self._collection

    def _build_filter(self, filters: dict[str, Any] | None = None) -> Filter | None:
        """Build a filter object from a dictionary of filter conditions.

        Args:
            filters: Dictionary of filter conditions

        Returns:
            Optional[Filter]: Constructed filter object or None if no filters
        """
        if not filters:
            logger.debug("No filters provided")
            return None

        logger.debug("Building filters from: %s", filters)
        filter_conditions = []
        for field, value in filters.items():
            if isinstance(value, (list, tuple)):
                logger.debug("Adding contains_any filter for field %s with values %s", field, value)
                filter_conditions.append(Filter.by_property(field).contains_any(value))
            else:
                logger.debug("Adding equals filter for field %s with value %s", field, value)
                filter_conditions.append(Filter.by_property(field).equal(value))

        if len(filter_conditions) == 1:
            return filter_conditions[0]

        # Combine filters with AND operator
        logger.debug("Combining %d filter conditions with AND", len(filter_conditions))
        result = filter_conditions[0]
        for f in filter_conditions[1:]:
            result = result & f
        return result

    def _get_include_properties(self, properties: list[str] | None = None) -> dict[str, Any]:
        """Get the properties to include in the query.

        Args:
            properties: List of property names to include

        Returns:
            Dict[str, Any]: Dictionary specifying properties to include
        """
        if not properties:
            logger.debug("No specific properties requested, including all")
            return {"additional": ["*"]}
        logger.debug("Including specific properties: %s", properties)
        return {"additional": properties}

    @with_weaviate_error_handling
    async def health_check(self) -> bool:
        """Check if repository is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            logger.debug("Performing health check")
            self._client.collections.list()
            logger.info("Health check passed")
            return True
        except Exception as e:
            logger.error("Health check failed: %s", str(e))
            return False
