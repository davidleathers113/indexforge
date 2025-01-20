"""Model factory implementations.

This module provides factory classes for creating and initializing ML models.
"""

import logging
from typing import Optional, TypeVar

import spacy
from sentence_transformers import SentenceTransformer
from spacy.language import Language

from src.services.ml.errors import ModelLoadError

from .parameters import EmbeddingParameters, ProcessingParameters

logger = logging.getLogger(__name__)

T = TypeVar("T", SentenceTransformer, Language)


class ModelFactory:
    """Base factory for ML model initialization."""

    def create_model(self, parameters: any) -> T:
        """Create and initialize a model.

        Args:
            parameters: Model parameters

        Returns:
            Initialized model

        Raises:
            ModelLoadError: If model initialization fails
        """
        raise NotImplementedError


class SpacyModelFactory(ModelFactory):
    """Factory for spaCy model initialization."""

    def __init__(self) -> None:
        """Initialize the factory."""
        try:
            import spacy

            self._spacy_available = True
        except ImportError:
            self._spacy_available = False

    def create_model(self, parameters: ProcessingParameters) -> Language:
        """Create and initialize a spaCy model.

        Args:
            parameters: Processing parameters

        Returns:
            Initialized spaCy model

        Raises:
            ModelLoadError: If model initialization fails
        """
        if not self._spacy_available:
            raise ModelLoadError(
                "spaCy is required for text processing",
                model_path=parameters.model_name,
                error_details={"missing_dependencies": ["spacy"]},
            )

        try:
            logger.info(f"Loading spaCy model: {parameters.model_name}")
            return spacy.load(parameters.model_name)
        except Exception as e:
            raise ModelLoadError(
                "Failed to load spaCy model",
                model_path=parameters.model_name,
                cause=e,
            ) from e


class SentenceTransformerFactory(ModelFactory):
    """Factory for SentenceTransformer model initialization."""

    def create_model(self, parameters: EmbeddingParameters) -> SentenceTransformer:
        """Create and initialize a SentenceTransformer model.

        Args:
            parameters: Embedding parameters

        Returns:
            Initialized SentenceTransformer model

        Raises:
            ModelLoadError: If model initialization fails
        """
        try:
            logger.info(f"Loading embedding model: {parameters.model_name}")
            return SentenceTransformer(
                parameters.model_name,
                device=parameters.device,
            )
        except Exception as e:
            raise ModelLoadError(
                "Failed to load embedding model",
                model_path=parameters.model_name,
                cause=e,
            ) from e
