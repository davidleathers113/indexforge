"""Search interfaces.

This module provides interfaces for vector-based search operations and
semantic similarity matching.
"""

from typing import TYPE_CHECKING, Any, Protocol, TypeVar


if TYPE_CHECKING:
    from src.core.models.chunks import Chunk
    from src.core.settings import Settings

T = TypeVar("T", bound="Chunk")


class VectorSearcher(Protocol):
    """Interface for vector-based search operations."""

    def __init__(self, settings: "Settings") -> None:
        """Initialize the searcher.

        Args:
            settings: Application settings

        Raises:
            ValueError: If required settings are missing
        """
        ...

    def search(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> list[tuple[T, float]]:
        """Perform semantic search.

        Args:
            query: Search query text
            limit: Maximum number of results to return
            min_score: Minimum similarity score threshold
            metadata: Optional search metadata

        Returns:
            List of tuples containing (chunk, score) where:
                - chunk: The matching chunk
                - score: Similarity score between 0 and 1

        Raises:
            ServiceStateError: If searcher is not initialized
            ValueError: If query is empty or parameters are invalid
            TypeError: If query is not a string
        """
        ...

    def find_similar(
        self,
        text: str,
        texts: list[str],
        limit: int | None = None,
        min_score: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> list[tuple[str, float]]:
        """Find similar texts from a list.

        Args:
            text: Query text to find similar matches for
            texts: List of texts to search through
            limit: Maximum number of results to return (None for all)
            min_score: Minimum similarity score threshold
            metadata: Optional similarity search metadata

        Returns:
            List of tuples containing (similar_text, score) where:
                - similar_text: The matching text
                - score: Similarity score between 0 and 1

        Raises:
            ServiceStateError: If searcher is not initialized
            ValueError: If text is empty or parameters are invalid
            TypeError: If inputs are not strings
        """
        ...

    def validate_query(self, query: str) -> list[str]:
        """Validate a search query.

        Args:
            query: Query to validate

        Returns:
            List of validation error messages, empty if valid

        Raises:
            TypeError: If query is not a string
        """
        ...
