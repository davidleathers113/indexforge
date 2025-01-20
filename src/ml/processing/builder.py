"""Builder for processed chunks.

This module provides a builder pattern implementation for constructing
processed chunks with NLP annotations and metadata.
"""

import logging
from typing import Any, Dict

from src.services.ml.entities import Chunk

logger = logging.getLogger(__name__)


class ProcessedChunkBuilder:
    """Builder for constructing processed chunks with NLP annotations."""

    def __init__(self, chunk: Chunk) -> None:
        """Initialize the builder.

        Args:
            chunk: Base chunk to process
        """
        self._chunk = chunk
        self._results: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}

    def add_result(self, strategy_name: str, result: Any) -> "ProcessedChunkBuilder":
        """Add processing result from a strategy.

        Args:
            strategy_name: Name of the processing strategy
            result: Processing result

        Returns:
            Self for method chaining
        """
        self._results[strategy_name] = result
        return self

    def add_metadata(self, key: str, value: Any) -> "ProcessedChunkBuilder":
        """Add metadata to the processed chunk.

        Args:
            key: Metadata key
            value: Metadata value

        Returns:
            Self for method chaining
        """
        self._metadata[key] = value
        return self

    def build(self) -> Dict[str, Any]:
        """Build the processed chunk.

        Returns:
            Dictionary containing the processed chunk data
        """
        return {
            "id": self._chunk.id,
            "content": self._chunk.content,
            "metadata": {
                **self._chunk.metadata,
                **self._metadata,
            },
            "results": self._results,
        }
