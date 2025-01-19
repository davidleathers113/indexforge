"""Core embedding service implementation.

This module provides the main embedding service interface, delegating specific
operations to specialized components.
"""

from typing import Any, List, Optional

import numpy as np
import numpy.typing as npt

from src.core import BaseService, Chunk, ChunkEmbedder
from src.core.settings import Settings
from src.ml.processing.models.service import ServiceState

from .config import GeneratorConfig, ValidatorConfig
from .decorators import track_metadata, validate_service_state
from .errors import GeneratorError
from .factory import EmbeddingGeneratorFactory
from .operations import EmbeddingOperations
from .validation.composite import CompositeValidator
from .validation.strategies import BasicValidator, SemanticValidator


class EmbeddingService(BaseService, ChunkEmbedder):
    """Embedding service for generating chunk embeddings."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the embedding service."""
        super().__init__()
        self._generator_config = GeneratorConfig(
            model_name=settings.embedding_model, batch_size=settings.batch_size
        )
        self._validator_config = ValidatorConfig()
        self._validator = CompositeValidator(
            [
                BasicValidator(),
                SemanticValidator(
                    min_words=self._validator_config.min_words,
                    min_size=self._validator_config.min_size,
                    max_size=self._validator_config.max_size,
                ),
            ]
        )
        self._operations = None

    async def initialize(self) -> None:
        """Initialize the service and its components."""
        self._transition_state(ServiceState.INITIALIZING)
        try:
            generator = EmbeddingGeneratorFactory.create_generator(
                model_name=self._generator_config.model_name,
                batch_size=self._generator_config.batch_size,
                device=self._generator_config.device,
            )
            self._operations = EmbeddingOperations(generator, self._validator)
            self._initialized = True
            self._transition_state(ServiceState.RUNNING)
        except Exception as e:
            self._transition_state(ServiceState.ERROR)
            raise GeneratorError(
                "Failed to initialize embedding service",
                model_name=self._generator_config.model_name,
                batch_size=self._generator_config.batch_size,
            ) from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._transition_state(ServiceState.STOPPING)
        self._operations = None
        self._transition_state(ServiceState.STOPPED)

    @track_metadata("last_embedding")
    @validate_service_state
    def embed_chunk(
        self, chunk: Chunk, metadata: Optional[dict[str, Any]] = None
    ) -> npt.NDArray[np.float32]:
        """Generate embedding for a chunk."""
        return self._operations.embed_chunk(chunk, metadata)

    @track_metadata("last_batch_embedding")
    @validate_service_state
    def embed_chunks(
        self, chunks: List[Chunk], metadata: Optional[dict[str, Any]] = None
    ) -> List[npt.NDArray[np.float32]]:
        """Generate embeddings for multiple chunks."""
        return self._operations.embed_chunks(chunks, metadata)
