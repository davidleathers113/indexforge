"""Model management for text processing.

This module provides factory and management classes for spaCy models,
ensuring proper initialization, configuration, and cleanup.
"""

import logging
from typing import Optional

try:
    import spacy
    from spacy.language import Language

    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

from src.services.ml.errors import ModelLoadError

logger = logging.getLogger(__name__)


class SpacyModelFactory:
    """Factory for creating and configuring spaCy models."""

    @staticmethod
    async def create_model(
        model_name: str, device: str = "cpu", disable: Optional[list[str]] = None
    ) -> Language:
        """Create and configure a spaCy model.

        Args:
            model_name: Name of the spaCy model to load
            device: Device to run model on (cpu/cuda)
            disable: Optional list of pipeline components to disable

        Returns:
            Configured spaCy model

        Raises:
            ModelLoadError: If model loading fails
        """
        if not SPACY_AVAILABLE:
            raise ModelLoadError(
                "spaCy is required for text processing",
                model_path=model_name,
                missing_dependencies=["spacy"],
            )

        try:
            logger.info(f"Loading spaCy model: {model_name}")
            nlp = spacy.load(model_name, disable=disable or [])
            if device != "cpu":
                nlp.to(device)
            return nlp
        except Exception as e:
            raise ModelLoadError("Failed to load spaCy model", model_path=model_name, cause=e)


class ProcessingModel:
    """Manager for spaCy model lifecycle.

    This class handles model initialization, configuration,
    and cleanup, ensuring proper resource management.
    """

    def __init__(
        self, model_name: str, device: str = "cpu", disable: Optional[list[str]] = None
    ) -> None:
        """Initialize the model manager.

        Args:
            model_name: Name of the spaCy model to use
            device: Device to run model on (cpu/cuda)
            disable: Optional list of pipeline components to disable
        """
        self._model: Optional[Language] = None
        self._model_name = model_name
        self._device = device
        self._disable = disable or []
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the spaCy model.

        Raises:
            ModelLoadError: If model initialization fails
        """
        if self._initialized:
            logger.warning("Model already initialized")
            return

        self._model = await SpacyModelFactory.create_model(
            self._model_name, self._device, self._disable
        )
        self._initialized = True
        logger.info(f"Model initialized: {self._model_name}")

    async def cleanup(self) -> None:
        """Clean up model resources."""
        if self._model is not None:
            # spaCy models don't require explicit cleanup,
            # but we'll reset our state
            self._model = None
            self._initialized = False
            logger.info("Model resources cleaned up")

    @property
    def model(self) -> Language:
        """Get the underlying spaCy model.

        Returns:
            spaCy Language model

        Raises:
            RuntimeError: If model is not initialized
        """
        if not self._initialized or self._model is None:
            raise RuntimeError("Model not initialized")
        return self._model

    @property
    def is_initialized(self) -> bool:
        """Check if model is initialized.

        Returns:
            True if model is initialized, False otherwise
        """
        return self._initialized
