"""Core chunk processing interfaces.

This module defines the interfaces for processing document chunks. It provides
abstract base classes for chunk processing, validation, and transformation.
"""

from abc import ABC, abstractmethod
from typing import List, Protocol, TypeVar

import numpy as np

from src.core.models.chunks import Chunk, ProcessedChunk
from src.core.models.documents import ProcessingStep

T = TypeVar("T", bound=Chunk)
P = TypeVar("P", bound=ProcessedChunk)


class ChunkValidator(Protocol):
    """Protocol for chunk validation."""

    def validate_chunk(self, chunk: Chunk) -> List[str]:
        """Validate a single chunk.

        Args:
            chunk: Chunk to validate

        Returns:
            List of validation error messages
        """
        ...

    def validate_chunks(self, chunks: List[Chunk]) -> List[str]:
        """Validate multiple chunks.

        Args:
            chunks: Chunks to validate

        Returns:
            List of validation error messages
        """
        ...


class ChunkProcessor(ABC):
    """Interface for chunk processing."""

    @abstractmethod
    def process_chunk(self, chunk: T) -> P:
        """Process a chunk.

        Args:
            chunk: Chunk to process

        Returns:
            Processed chunk
        """
        pass

    @abstractmethod
    def process_chunks(self, chunks: List[T]) -> List[P]:
        """Process multiple chunks.

        Args:
            chunks: Chunks to process

        Returns:
            List of processed chunks
        """
        pass

    @abstractmethod
    def validate_chunk(self, chunk: T) -> List[str]:
        """Validate a chunk before processing.

        Args:
            chunk: Chunk to validate

        Returns:
            List of validation error messages
        """
        pass


class ChunkEmbedder(ChunkProcessor):
    """Interface for chunk embedding."""

    @abstractmethod
    def embed_chunk(self, chunk: T) -> np.ndarray:
        """Generate embedding for a chunk.

        Args:
            chunk: Chunk to embed

        Returns:
            Vector embedding of chunk content
        """
        pass

    @abstractmethod
    def embed_chunks(self, chunks: List[T]) -> List[np.ndarray]:
        """Generate embeddings for multiple chunks.

        Args:
            chunks: Chunks to embed

        Returns:
            List of vector embeddings
        """
        pass


class ChunkTransformer(ChunkProcessor):
    """Interface for chunk transformation."""

    @abstractmethod
    def transform_chunk(self, chunk: T, **kwargs) -> P:
        """Transform a chunk.

        Args:
            chunk: Chunk to transform
            **kwargs: Additional transformation parameters

        Returns:
            Transformed chunk
        """
        pass

    @abstractmethod
    def transform_chunks(self, chunks: List[T], **kwargs) -> List[P]:
        """Transform multiple chunks.

        Args:
            chunks: Chunks to transform
            **kwargs: Additional transformation parameters

        Returns:
            List of transformed chunks
        """
        pass

    @abstractmethod
    def get_transformation_steps(self) -> List[ProcessingStep]:
        """Get transformation processing steps.

        Returns:
            List of processing steps
        """
        pass


class TextProcessor(ABC):
    """Interface for text processing operations."""

    @abstractmethod
    def clean_text(self, text: str) -> str:
        """Clean and normalize text.

        Args:
            text: Input text to clean

        Returns:
            Cleaned text

        Raises:
            ServiceStateError: If service is not initialized
        """
        pass

    @abstractmethod
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences.

        Args:
            text: Input text to split

        Returns:
            List of sentences

        Raises:
            ServiceStateError: If service is not initialized
        """
        pass

    @abstractmethod
    def chunk_text(self, text: str, max_chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks.

        Args:
            text: Input text to chunk
            max_chunk_size: Maximum size of each chunk
            overlap: Number of characters to overlap between chunks

        Returns:
            List of text chunks

        Raises:
            ServiceStateError: If service is not initialized
        """
        pass
