"""Test fixtures for embedding service tests."""

from dataclasses import dataclass
from typing import Optional

from src.services.ml.implementations import EmbeddingParameters, EmbeddingService


@dataclass
class EmbeddingServiceFactory:
    """Factory for creating embedding service test instances.

    This factory provides methods for creating EmbeddingService instances
    with various configurations for testing purposes.
    """

    model_name: str = "all-MiniLM-L6-v2"
    batch_size: int = 32
    min_text_length: int = 1
    max_text_length: int = 512

    def with_model(self, model_name: str) -> "EmbeddingServiceFactory":
        """Set the model name.

        Args:
            model_name: Name of the embedding model to use

        Returns:
            Self for method chaining
        """
        self.model_name = model_name
        return self

    def with_batch_size(self, batch_size: int) -> "EmbeddingServiceFactory":
        """Set the batch size.

        Args:
            batch_size: Size of batches for processing

        Returns:
            Self for method chaining
        """
        self.batch_size = batch_size
        return self

    def with_text_length_constraints(
        self, min_length: Optional[int] = None, max_length: Optional[int] = None
    ) -> "EmbeddingServiceFactory":
        """Set text length constraints.

        Args:
            min_length: Minimum text length (if None, uses default)
            max_length: Maximum text length (if None, uses default)

        Returns:
            Self for method chaining
        """
        if min_length is not None:
            self.min_text_length = min_length
        if max_length is not None:
            self.max_text_length = max_length
        return self

    def create(self) -> EmbeddingService:
        """Create a new EmbeddingService instance.

        Returns:
            Configured EmbeddingService instance
        """
        params = EmbeddingParameters(
            model_name=self.model_name,
            batch_size=self.batch_size,
            min_text_length=self.min_text_length,
            max_text_length=self.max_text_length,
        )
        return EmbeddingService(params)

    @classmethod
    def default(cls) -> EmbeddingService:
        """Create a service with default configuration.

        Returns:
            EmbeddingService with default parameters
        """
        return cls().create()

    @classmethod
    def invalid(cls) -> EmbeddingService:
        """Create a service with invalid configuration.

        Returns:
            EmbeddingService with non-existent model
        """
        return cls().with_model("non-existent-model").create()
