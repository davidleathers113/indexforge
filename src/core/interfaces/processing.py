"""Core chunk processing interfaces.

This module defines the interfaces for processing document chunks. It provides
protocols for chunk processing, validation, transformation, and text processing
operations.
"""

from typing import TYPE_CHECKING, Any, Protocol, TypeVar


if TYPE_CHECKING:
    import numpy as np

    from src.core.models.chunks import Chunk, ProcessedChunk
    from src.core.models.documents import ProcessingStep
    from src.core.settings import Settings

T = TypeVar("T", bound="Chunk")
P = TypeVar("P", bound="ProcessedChunk")


class ChunkValidator(Protocol):
    """Protocol for chunk validation operations."""

    def validate_chunk(self, chunk: "Chunk") -> list[str]:
        """Validate a single chunk.

        Args:
            chunk (Chunk): Chunk to validate

        Returns:
            List[str]: List of validation error messages, empty if valid

        Raises:
            ValueError: If chunk is malformed
            TypeError: If chunk is not of correct type
        """
        ...

    def validate_chunks(self, chunks: list["Chunk"]) -> list[str]:
        """Validate multiple chunks.

        Args:
            chunks (List[Chunk]): Chunks to validate

        Returns:
            List[str]: List of validation error messages, empty if all valid

        Raises:
            ValueError: If any chunk is malformed
            TypeError: If any chunk is not of correct type
        """
        ...


class ChunkProcessor(Protocol):
    """Protocol for chunk processing operations."""

    def __init__(self, settings: "Settings") -> None:
        """Initialize the processor.

        Args:
            settings (Settings): Application settings

        Raises:
            ValueError: If required settings are missing
        """
        ...

    def process_chunk(self, chunk: T, metadata: dict[str, Any] | None = None) -> P:
        """Process a chunk.

        Args:
            chunk (T): Chunk to process
            metadata (Optional[Dict[str, Any]], optional): Processing metadata.
                Defaults to None.

        Returns:
            P: Processed chunk

        Raises:
            ServiceStateError: If processor is not initialized
            ValueError: If chunk is invalid
            TypeError: If chunk is not of correct type
        """
        ...

    def process_chunks(self, chunks: list[T], metadata: dict[str, Any] | None = None) -> list[P]:
        """Process multiple chunks.

        Args:
            chunks (List[T]): Chunks to process
            metadata (Optional[Dict[str, Any]], optional): Processing metadata.
                Defaults to None.

        Returns:
            List[P]: List of processed chunks

        Raises:
            ServiceStateError: If processor is not initialized
            ValueError: If any chunk is invalid
            TypeError: If any chunk is not of correct type
        """
        ...

    def validate_chunk(self, chunk: T) -> list[str]:
        """Validate a chunk before processing.

        Args:
            chunk (T): Chunk to validate

        Returns:
            List[str]: List of validation error messages, empty if valid

        Raises:
            TypeError: If chunk is not of correct type
        """
        ...

    def get_processing_steps(self) -> list["ProcessingStep"]:
        """Get processing steps applied by this processor.

        Returns:
            List[ProcessingStep]: List of processing steps
        """
        ...


class ChunkEmbedder(Protocol):
    """Protocol for chunk embedding operations."""

    def __init__(self, settings: "Settings") -> None:
        """Initialize the embedder.

        Args:
            settings (Settings): Application settings

        Raises:
            ValueError: If required settings are missing
        """
        ...

    def embed_chunk(self, chunk: T, metadata: dict[str, Any] | None = None) -> "np.ndarray":
        """Generate embedding for a chunk.

        Args:
            chunk (T): Chunk to embed
            metadata (Optional[Dict[str, Any]], optional): Embedding metadata.
                Defaults to None.

        Returns:
            np.ndarray: Vector embedding of chunk content

        Raises:
            ServiceStateError: If embedder is not initialized
            ValueError: If chunk is invalid
            TypeError: If chunk is not of correct type
        """
        ...

    def embed_chunks(
        self, chunks: list[T], metadata: dict[str, Any] | None = None
    ) -> list["np.ndarray"]:
        """Generate embeddings for multiple chunks.

        Args:
            chunks (List[T]): Chunks to embed
            metadata (Optional[Dict[str, Any]], optional): Embedding metadata.
                Defaults to None.

        Returns:
            List[np.ndarray]: List of vector embeddings

        Raises:
            ServiceStateError: If embedder is not initialized
            ValueError: If any chunk is invalid
            TypeError: If any chunk is not of correct type
        """
        ...

    def validate_chunk(self, chunk: T) -> list[str]:
        """Validate a chunk before embedding.

        Args:
            chunk (T): Chunk to validate

        Returns:
            List[str]: List of validation error messages, empty if valid

        Raises:
            TypeError: If chunk is not of correct type
        """
        ...


class ChunkTransformer(Protocol):
    """Protocol for chunk transformation operations."""

    def __init__(self, settings: "Settings") -> None:
        """Initialize the transformer.

        Args:
            settings (Settings): Application settings

        Raises:
            ValueError: If required settings are missing
        """
        ...

    def transform_chunk(self, chunk: T, metadata: dict[str, Any] | None = None) -> P:
        """Transform a chunk.

        Args:
            chunk (T): Chunk to transform
            metadata (Optional[Dict[str, Any]], optional): Transformation metadata.
                Defaults to None.

        Returns:
            P: Transformed chunk

        Raises:
            ServiceStateError: If transformer is not initialized
            ValueError: If chunk is invalid
            TypeError: If chunk is not of correct type
        """
        ...

    def transform_chunks(
        self, chunks: list[T], metadata: dict[str, Any] | None = None
    ) -> list[P]:
        """Transform multiple chunks.

        Args:
            chunks (List[T]): Chunks to transform
            metadata (Optional[Dict[str, Any]], optional): Transformation metadata.
                Defaults to None.

        Returns:
            List[P]: List of transformed chunks

        Raises:
            ServiceStateError: If transformer is not initialized
            ValueError: If any chunk is invalid
            TypeError: If any chunk is not of correct type
        """
        ...

    def get_transformation_steps(self) -> list["ProcessingStep"]:
        """Get transformation processing steps.

        Returns:
            List[ProcessingStep]: List of processing steps applied during transformation
        """
        ...

    def validate_chunk(self, chunk: T) -> list[str]:
        """Validate a chunk before transformation.

        Args:
            chunk (T): Chunk to validate

        Returns:
            List[str]: List of validation error messages, empty if valid

        Raises:
            TypeError: If chunk is not of correct type
        """
        ...


class TextProcessor(Protocol):
    """Protocol for text processing operations."""

    def __init__(self, settings: "Settings") -> None:
        """Initialize the processor.

        Args:
            settings (Settings): Application settings

        Raises:
            ValueError: If required settings are missing
        """
        ...

    def clean_text(self, text: str, metadata: dict[str, Any] | None = None) -> str:
        """Clean and normalize text.

        Args:
            text (str): Input text to clean
            metadata (Optional[Dict[str, Any]], optional): Cleaning metadata.
                Defaults to None.

        Returns:
            str: Cleaned and normalized text

        Raises:
            ServiceStateError: If processor is not initialized
            ValueError: If text is empty or invalid
            TypeError: If text is not a string
        """
        ...

    def split_into_sentences(
        self, text: str, metadata: dict[str, Any] | None = None
    ) -> list[str]:
        """Split text into sentences.

        Args:
            text (str): Input text to split
            metadata (Optional[Dict[str, Any]], optional): Splitting metadata.
                Defaults to None.

        Returns:
            List[str]: List of sentences

        Raises:
            ServiceStateError: If processor is not initialized
            ValueError: If text is empty or invalid
            TypeError: If text is not a string
        """
        ...

    def chunk_text(
        self,
        text: str,
        max_chunk_size: int = 1000,
        overlap: int = 100,
        metadata: dict[str, Any] | None = None,
    ) -> list[str]:
        """Split text into overlapping chunks.

        Args:
            text (str): Input text to chunk
            max_chunk_size (int, optional): Maximum size of each chunk. Defaults to 1000.
            overlap (int, optional): Number of characters to overlap between chunks.
                Defaults to 100.
            metadata (Optional[Dict[str, Any]], optional): Chunking metadata.
                Defaults to None.

        Returns:
            List[str]: List of text chunks

        Raises:
            ServiceStateError: If processor is not initialized
            ValueError: If text is empty, max_chunk_size <= 0, or overlap < 0
            TypeError: If text is not a string
        """
        ...

    def validate_text(self, text: str) -> list[str]:
        """Validate text before processing.

        Args:
            text (str): Text to validate

        Returns:
            List[str]: List of validation error messages, empty if valid

        Raises:
            TypeError: If text is not a string
        """
        ...
