"""Statistics service for handling document collection statistics."""

import logging

from src.api.repositories.weaviate_repo import WeaviateRepository

logger = logging.getLogger(__name__)


class StatisticsService:
    """Fetches document statistics."""

    def __init__(self, repository: WeaviateRepository):
        """Initialize the statistics service.

        Args:
            repository: Repository for data access
        """
        self._repository = repository

    async def get_stats(self) -> dict:
        """Get document collection statistics.

        Returns:
            Dictionary containing collection statistics
        """
        return await self._repository.get_stats()
