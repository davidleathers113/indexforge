"""Utility for generating embeddings from text.

This module provides functionality for generating embeddings from text using
various embedding models. It supports different embedding strategies and
configurations.

Classes:
    EmbeddingGenerator: Main class for generating embeddings from text.

Example:
    ```python
    generator = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")
    embeddings = generator.generate_embeddings(["some text", "more text"])
    ```
"""

from typing import List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingGenerator:
    """Generates embeddings from text using sentence transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the embedding generator.

        Args:
            model_name: Name of the sentence transformer model to use.
                Defaults to "all-MiniLM-L6-v2".
        """
        self.model = SentenceTransformer(model_name)

    def generate_embeddings(self, texts: List[str], batch_size: Optional[int] = None) -> np.ndarray:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of texts to generate embeddings for.
            batch_size: Optional batch size for processing. If None,
                uses the model's default batch size.

        Returns:
            Array of embeddings, shape (len(texts), embedding_dim).
        """
        return self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
