"""Base embedding functionality.

This module provides the core embedding generation capabilities using
transformer models.
"""

import logging
from typing import List, Optional, Protocol, runtime_checkable

import numpy as np
import numpy.typing as npt
from sentence_transformers import SentenceTransformer

from src.ml.exceptions import InputValidationError, ModelInitError

logger = logging.getLogger(__name__)


@runtime_checkable
class EmbeddingGenerator(Protocol):
    """Protocol defining the interface for embedding generators."""

    def generate_embeddings(self, texts: List[str]) -> npt.NDArray[np.float32]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to generate embeddings for

        Returns:
            Array of embeddings, shape (len(texts), embedding_dim)

        Raises:
            ValueError: If texts is empty or contains invalid items
            RuntimeError: If embedding generation fails
        """
        ...


class BaseEmbeddingGenerator:
    """Base class for text embedding generation using transformer models."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None,
        batch_size: int = 32,
    ) -> None:
        """Initialize the embedding generator.

        Args:
            model_name: Name of the transformer model to use
            device: Device to run the model on ('cpu', 'cuda', etc.)
            batch_size: Default batch size for processing

        Raises:
            ModelInitError: If model initialization fails
        """
        try:
            self.model = SentenceTransformer(model_name, device=device)
            self.batch_size = batch_size
            logger.info(
                "Initialized BaseEmbeddingGenerator with model=%s, device=%s",
                model_name,
                self.model.device,
            )
        except Exception as e:
            logger.exception("Failed to initialize embedding model")
            raise ModelInitError("Failed to initialize embedding model") from e

    def generate_embeddings(self, texts: List[str], batch_size: Optional[int] = None) -> np.ndarray:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of texts to generate embeddings for
            batch_size: Optional batch size override

        Returns:
            Array of embeddings with shape (n_texts, embedding_dim)

        Raises:
            InputValidationError: If texts is empty or contains invalid values
            RuntimeError: If embedding generation fails
        """
        if not texts:
            raise InputValidationError("No texts provided for embedding generation")

        if not all(isinstance(text, str) for text in texts):
            raise InputValidationError("All inputs must be strings")

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size or self.batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            logger.debug(
                "Generated embeddings for %d texts with shape %s",
                len(texts),
                embeddings.shape,
            )
            return embeddings
        except Exception as e:
            logger.exception("Failed to generate embeddings")
            raise RuntimeError("Failed to generate embeddings") from e

    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embeddings produced by the model.

        Returns:
            Embedding dimension
        """
        return self.model.get_sentence_embedding_dimension()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        # SentenceTransformer handles its own cleanup
        pass
