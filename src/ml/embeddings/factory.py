"""Factory for creating embedding generators.

This module provides factory methods for creating and configuring
embedding generators with appropriate settings.
"""

from typing import Optional

from .base import BaseEmbeddingGenerator


class EmbeddingGeneratorFactory:
    """Factory for creating embedding generators.

    This class encapsulates the logic for creating and configuring
    embedding generators with appropriate settings.
    """

    @staticmethod
    def create_generator(
        model_name: str,
        batch_size: int,
        device: Optional[str] = None,
    ) -> BaseEmbeddingGenerator:
        """Create a new embedding generator.

        Args:
            model_name: Name of the transformer model to use
            batch_size: Batch size for processing
            device: Optional device to run the model on

        Returns:
            Configured embedding generator instance

        Raises:
            ValueError: If model_name is empty or batch_size is invalid
        """
        if not model_name:
            raise ValueError("model_name cannot be empty")
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")

        return BaseEmbeddingGenerator(
            model_name=model_name,
            device=device,
            batch_size=batch_size,
        )
