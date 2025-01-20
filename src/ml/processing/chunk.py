"""Chunk processor implementation.

Note: This implementation is deprecated. Use src.services.ml.implementations.processing instead.
"""

import logging
from typing import Any, Dict, List, Optional

from src.core.models.chunks import Chunk
from src.core.settings import Settings
from src.services.ml.implementations import ProcessingService as NewProcessingService
from src.services.ml.implementations.processing import ProcessingParameters

logger = logging.getLogger(__name__)


class ChunkProcessor:
    """Processor for text chunks with NLP capabilities.

    Note: This class is deprecated. Use src.services.ml.implementations.processing.ProcessingService instead.
    This class maintains backward compatibility while delegating to the new implementation.

    Attributes:
        settings: Application settings
        nlp: spaCy language model
        strategy_manager: Manager for processing strategies
    """

    def __init__(self, settings: "Settings") -> None:
        """Initialize the processor.

        Args:
            settings: Application settings

        Raises:
            ValueError: If required settings are missing
        """
        self._service = NewProcessingService(
            ProcessingParameters(
                model_name="en_core_web_sm",
                min_text_length=10,
                max_text_length=1000000,
                min_words=3,
            )
        )
        logger.warning(
            "Using deprecated chunk processor implementation. "
            "Use src.services.ml.implementations.processing.ProcessingService instead."
        )

    async def initialize(self) -> None:
        """Initialize NLP components and models.

        Raises:
            ServiceInitializationError: If initialization fails
        """
        await self._service.initialize()

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self._service.cleanup()

    def process_chunk(
        self, chunk: Chunk, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a single chunk.

        Args:
            chunk: Chunk to process
            metadata: Optional processing metadata

        Returns:
            Processed chunk with NLP annotations

        Raises:
            ServiceStateError: If processor is not initialized
            ValidationError: If chunk is invalid
            TypeError: If chunk is not of correct type
        """
        return self._service.process_chunk(chunk, metadata)

    def process_chunks(
        self, chunks: List[Chunk], metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Process multiple chunks.

        Args:
            chunks: Chunks to process
            metadata: Optional processing metadata

        Returns:
            List of processed chunks

        Raises:
            ServiceStateError: If processor is not initialized
            ValidationError: If any chunk is invalid
            TypeError: If any chunk is not of correct type
        """
        return self._service.process_chunks(chunks, metadata)
