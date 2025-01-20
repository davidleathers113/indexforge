"""Processing service implementation.

This module provides the processing service that applies NLP operations
to text chunks using spaCy and custom processing strategies.
"""

import logging
from typing import Any, Dict, List, Optional

from spacy.language import Language

from src.core.models.chunks import Chunk
from src.core.settings import Settings
from src.services.ml.errors import ProcessingError
from src.services.ml.service import MLService
from src.services.ml.validation.processing import create_processing_validator

from .factories import SpacyModelFactory
from .lifecycle import ServiceLifecycle
from .parameters import ProcessingParameters
from .validation import ValidationManager

logger = logging.getLogger(__name__)


class ProcessingService(MLService[Language, ProcessingParameters]):
    """Service for text processing operations."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the processing service.

        Args:
            settings: Application settings
        """
        super().__init__()
        self._lifecycle = ServiceLifecycle(
            settings, SpacyModelFactory(), create_processing_validator
        )
        self._validation: Optional[ValidationManager] = None

    async def _load_parameters(self) -> ProcessingParameters:
        """Load processing parameters from settings."""
        return ProcessingParameters(
            model_name=self._settings.processing_model,
            batch_size=self._settings.batch_size,
            min_text_length=self._settings.min_text_length,
            max_text_length=self._settings.max_text_length,
            min_words=self._settings.min_words,
            max_memory_mb=self._settings.max_memory_mb,
            enable_ner=self._settings.enable_ner,
            enable_sentiment=self._settings.enable_sentiment,
            enable_topics=self._settings.enable_topics,
            required_metadata_fields=self._settings.required_metadata_fields,
            optional_metadata_fields=self._settings.optional_metadata_fields,
        )

    async def load_model(self, parameters: ProcessingParameters) -> Language:
        """Load and initialize the service."""
        await self._lifecycle.initialize(parameters)
        self._validation = ValidationManager(self._lifecycle.validator)
        return self._lifecycle.model

    def process_chunk(
        self, chunk: Chunk, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a single chunk."""
        try:
            self._validation.validate_chunk(chunk)
            return self._lifecycle.processor.process(chunk, metadata)
        except Exception as e:
            raise ProcessingError(
                "Failed to process chunk",
                input_details={"chunk_id": chunk.id},
                cause=e,
            ) from e

    def process_chunks(
        self, chunks: List[Chunk], metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Process multiple chunks."""
        try:
            self._validation.validate_chunks(chunks)
            return [self.process_chunk(chunk, metadata) for chunk in chunks]
        except Exception as e:
            raise ProcessingError(
                "Failed to process chunks",
                input_details={"chunk_count": len(chunks)},
                cause=e,
            ) from e
