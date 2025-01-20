"""Core processor implementation.

This module provides the main processor for applying NLP operations
to text chunks using registered strategies.
"""

import logging
from typing import Any, Dict, List, Optional

from src.services.ml.entities import Chunk
from src.services.ml.errors import ProcessingError

from .builder import ProcessedChunkBuilder
from .model import ProcessingModel
from .registry import StrategyRegistry

logger = logging.getLogger(__name__)


class ChunkProcessor:
    """Processor for applying NLP operations to text chunks.

    This class coordinates the processing of text chunks using
    registered strategies and the spaCy model.
    """

    def __init__(self, model: ProcessingModel, registry: StrategyRegistry) -> None:
        """Initialize the processor.

        Args:
            model: Initialized processing model
            registry: Strategy registry
        """
        self._model = model
        self._registry = registry

    async def process_chunk(
        self, chunk: Chunk, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a single chunk.

        Args:
            chunk: Chunk to process
            metadata: Optional processing metadata

        Returns:
            Processed chunk data

        Raises:
            ProcessingError: If processing fails
        """
        try:
            # Create builder for this chunk
            builder = ProcessedChunkBuilder(chunk)

            # Add processing metadata
            if metadata:
                for key, value in metadata.items():
                    builder.add_metadata(key, value)
            builder.add_metadata("content_length", len(chunk.content))

            # Process with all strategies
            for name, strategy in self._registry.strategies.items():
                try:
                    result = strategy.process(chunk.content, metadata)
                    builder.add_result(name, result)
                except Exception as e:
                    logger.exception(f"Strategy {name} failed")
                    raise ProcessingError(
                        f"Strategy {name} failed: {e}",
                        input_details={
                            "chunk_id": chunk.id,
                            "strategy": name,
                        },
                        cause=e,
                    )

            return builder.build()

        except Exception as e:
            if not isinstance(e, ProcessingError):
                logger.exception("Processing failed")
                raise ProcessingError(
                    "Failed to process chunk",
                    input_details={"chunk_id": chunk.id},
                    cause=e,
                )
            raise

    async def process_chunks(
        self, chunks: List[Chunk], metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Process multiple chunks.

        Args:
            chunks: Chunks to process
            metadata: Optional processing metadata

        Returns:
            List of processed chunk data

        Raises:
            ProcessingError: If processing fails
        """
        try:
            # Add batch metadata
            batch_metadata = metadata or {}
            batch_metadata["batch_size"] = len(chunks)

            # Process all chunks
            results = []
            for i, chunk in enumerate(chunks):
                try:
                    chunk_metadata = {
                        **batch_metadata,
                        "batch_index": i,
                    }
                    result = await self.process_chunk(chunk, chunk_metadata)
                    results.append(result)
                except Exception as e:
                    logger.exception(f"Failed to process chunk at index {i}")
                    raise ProcessingError(
                        f"Failed to process chunk at index {i}",
                        input_details={
                            "chunk_id": chunk.id,
                            "batch_index": i,
                        },
                        cause=e,
                    )

            return results

        except Exception as e:
            if not isinstance(e, ProcessingError):
                logger.exception("Batch processing failed")
                raise ProcessingError(
                    "Failed to process chunks",
                    input_details={"chunk_count": len(chunks)},
                    cause=e,
                )
            raise
