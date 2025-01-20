"""Service lifecycle management.

This module handles service initialization, state management, and resource cleanup.
"""

import logging
from typing import Generic, Optional, TypeVar

from sentence_transformers import SentenceTransformer
from spacy.language import Language

from src.core.settings import Settings
from src.services.ml.errors import ServiceNotInitializedError
from src.services.ml.validation import CompositeValidator

from .factories import ModelFactory, SentenceTransformerFactory, SpacyModelFactory
from .parameters import BaseParameters, EmbeddingParameters, ProcessingParameters
from .processors import EmbeddingProcessor, ProcessorStrategy, SpacyProcessor

logger = logging.getLogger(__name__)

T = TypeVar("T", SentenceTransformer, Language)
P = TypeVar("P", bound=BaseParameters)


class ServiceLifecycle(Generic[T, P]):
    """Manages service initialization and state."""

    def __init__(
        self, settings: Settings, factory: ModelFactory, validator_creator: callable
    ) -> None:
        """Initialize lifecycle manager.

        Args:
            settings: Application settings
            factory: Model factory instance
            validator_creator: Function to create validator
        """
        self._settings = settings
        self._factory = factory
        self._validator_creator = validator_creator
        self._model: Optional[T] = None
        self._processor: Optional[ProcessorStrategy] = None
        self._validator: Optional[CompositeValidator] = None

    async def initialize(self, params: P) -> None:
        """Initialize service components.

        Args:
            params: Service parameters

        Raises:
            ServiceNotInitializedError: If initialization fails
        """
        try:
            self._model = self._factory.create_model(params)
            self._validator = self._validator_creator(
                min_text_length=params.min_text_length,
                max_text_length=params.max_text_length,
                min_words=params.min_words,
                required_metadata_fields=params.required_metadata_fields,
                optional_metadata_fields=params.optional_metadata_fields,
            )
            self._initialize_processor(params)
            logger.info("Service initialization complete")
        except Exception as e:
            logger.error("Service initialization failed", exc_info=e)
            raise ServiceNotInitializedError("Failed to initialize service") from e

    def _initialize_processor(self, params: P) -> None:
        """Initialize the appropriate processor.

        Args:
            params: Service parameters
        """
        if isinstance(params, ProcessingParameters):
            self._processor = SpacyProcessor(self._model, params)
        elif isinstance(params, EmbeddingParameters):
            self._processor = EmbeddingProcessor(self._model, params)

    @property
    def processor(self) -> ProcessorStrategy:
        """Get the initialized processor.

        Returns:
            Initialized processor

        Raises:
            ServiceNotInitializedError: If processor not initialized
        """
        if not self._processor:
            raise ServiceNotInitializedError("Processor not initialized")
        return self._processor

    @property
    def validator(self) -> CompositeValidator:
        """Get the initialized validator.

        Returns:
            Initialized validator

        Raises:
            ServiceNotInitializedError: If validator not initialized
        """
        if not self._validator:
            raise ServiceNotInitializedError("Validator not initialized")
        return self._validator
