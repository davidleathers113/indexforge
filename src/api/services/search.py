"""Search service for document operations."""

import logging
from typing import Optional

from src.api.models.requests import DocumentFilter, SearchQuery
from src.api.models.responses import SearchResponse, Stats
from src.api.repositories.weaviate_repo import WeaviateRepository

logger = logging.getLogger(__name__)


class SearchService:
    """Service for search operations."""

    def __init__(self, repository: WeaviateRepository):
        """Initialize service with repository.

        Args:
            repository: Repository for data access
        """
        self._repository = repository

    async def search_documents(
        self, query: SearchQuery, filter_params: Optional[DocumentFilter] = None
    ) -> SearchResponse:
        """Search documents with optional filtering.

        Args:
            query: Search parameters
            filter_params: Optional filter criteria

        Returns:
            SearchResponse containing results and metadata
        """
        try:
            if filter_params:
                # If we have filters, use filter-based search
                return await self._repository.filter_documents(
                    filter_params=filter_params, limit=query.limit, offset=query.offset
                )

            # Otherwise use semantic search
            return await self._repository.search(query)

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise

    async def get_stats(self) -> Stats:
        """Get collection statistics.

        Returns:
            Stats containing document counts and status
        """
        try:
            return await self._repository.get_stats()
        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}")
            raise
