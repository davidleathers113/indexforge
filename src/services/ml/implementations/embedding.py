"""Embedding service implementation.

This module provides the embedding service that generates vector embeddings
for text chunks using ML models.
"""

import logging
from typing import Any, Dict, List, Optional

from sentence_transformers import SentenceTransformer

from src.core.models.chunks import Chunk
from src.core.settings import Settings
from src.services.ml.errors import ProcessingError
from src.services.ml.service import MLService
from src.services.ml.validation.embedding import create_embedding_validator

from .factories import SentenceTransformerFactory
from .lifecycle import ServiceLifecycle
from .parameters import EmbeddingParameters
from .validation import ValidationManager

logger = logging.getLogger(__name__)


class EmbeddingService(MLService[SentenceTransformer, EmbeddingParameters]):
    """Service for generating text embeddings."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the embedding service.

        Args:
            settings: Application settings
        """
        super().__init__()
        self._lifecycle = ServiceLifecycle(
            settings, SentenceTransformerFactory(), create_embedding_validator
        )
        self._validation: Optional[ValidationManager] = None

    async def _load_parameters(self) -> EmbeddingParameters:
        """Load embedding parameters from settings."""
        return EmbeddingParameters(
            model_name=self._settings.embedding_model,
            batch_size=self._settings.batch_size,
            device=self._settings.device,
            min_text_length=self._settings.min_text_length,
            max_text_length=self._settings.max_text_length,
            min_words=self._settings.min_words,
            required_metadata_fields=self._settings.required_metadata_fields,
            optional_metadata_fields=self._settings.optional_metadata_fields,
        )

    async def load_model(self, parameters: EmbeddingParameters) -> SentenceTransformer:
        """Load and initialize the service."""
        await self._lifecycle.initialize(parameters)
        self._validation = ValidationManager(self._lifecycle.validator)
        return self._lifecycle.model

    def embed_chunk(
        self, chunk: Chunk, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate embedding for a chunk."""
        try:
            self._validation.validate_chunk(chunk)
            return self._lifecycle.processor.process(chunk, metadata)
        except Exception as e:
            raise ProcessingError(
                "Failed to generate embedding",
                input_details={"chunk_id": chunk.id},
                cause=e,
            ) from e

    def embed_chunks(
        self, chunks: List[Chunk], metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Generate embeddings for multiple chunks."""
        try:
            self._validation.validate_chunks(chunks)
            return [self.embed_chunk(chunk, metadata) for chunk in chunks]
        except Exception as e:
            raise ProcessingError(
                "Failed to generate embeddings",
                input_details={"chunk_count": len(chunks)},
                cause=e,
            ) from e
