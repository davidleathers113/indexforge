"""Text processor implementation.

This module provides the main text processor class that integrates
cleaning, chunking, and analysis functionality.
"""

from typing import Any, Dict, List, Optional

from src.core.interfaces.processing import TextProcessor as TextProcessorProtocol
from src.core.settings import Settings
from src.ml.processing.base import BaseProcessor
from src.ml.processing.errors import ServiceStateError
from src.ml.processing.text.analysis import detect_language, validate_content
from src.ml.processing.text.chunking import chunk_text
from src.ml.processing.text.cleaning import clean_text
from src.ml.processing.text.config import TextProcessingConfig


class TextProcessor(BaseProcessor, TextProcessorProtocol):
    """Text processor implementation.

    Provides functionality for text cleaning, chunking, and analysis
    with configurable settings and metadata tracking.
    """

    def __init__(self, settings: Settings, config: Optional[TextProcessingConfig] = None) -> None:
        """Initialize the text processor.

        Args:
            settings: Application settings
            config: Optional text processing configuration

        Raises:
            ValueError: If required settings are missing
        """
        super().__init__(settings)
        self._config = config or TextProcessingConfig()
        self._processed_texts: List[str] = []

    def clean_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Clean and normalize text.

        Args:
            text: Input text to clean
            metadata: Optional metadata to track

        Returns:
            Cleaned text

        Raises:
            ServiceStateError: If processor is not initialized
            ValueError: If text is empty or invalid
            TypeError: If text is not a string
        """
        if not self.is_initialized:
            raise ServiceStateError("Processor is not initialized")

        if not isinstance(text, str):
            raise TypeError("Input text must be a string")

        # Clean text
        cleaned = clean_text(text)

        # Track metadata if provided
        if metadata is not None:
            metadata["original_length"] = len(text)
            metadata["cleaned_length"] = len(cleaned)

        # Track processed text
        self._processed_texts.append(cleaned)

        return cleaned

    def split_into_sentences(
        self, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Split text into sentences.

        Args:
            text: Input text to split
            metadata: Optional metadata to track

        Returns:
            List of sentences

        Raises:
            ServiceStateError: If processor is not initialized
            ValueError: If text is empty or invalid
            TypeError: If text is not a string
        """
        if not self.is_initialized:
            raise ServiceStateError("Processor is not initialized")

        if not isinstance(text, str):
            raise TypeError("Input text must be a string")

        # Clean text first
        text = self.clean_text(text)

        # Split into chunks with sentence boundaries
        sentences = chunk_text(
            text,
            max_size=self._config.max_chunk_size,
            overlap=0,  # No overlap for sentences
            preserve_paragraphs=False,
        )

        # Track metadata if provided
        if metadata is not None:
            metadata["num_sentences"] = len(sentences)
            metadata["avg_sentence_length"] = (
                sum(len(s) for s in sentences) / len(sentences) if sentences else 0
            )

        return sentences

    def chunk_text(
        self,
        text: str,
        max_chunk_size: Optional[int] = None,
        overlap: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Split text into overlapping chunks.

        Args:
            text: Input text to chunk
            max_chunk_size: Maximum size of each chunk
            overlap: Number of characters to overlap
            metadata: Optional metadata to track

        Returns:
            List of text chunks

        Raises:
            ServiceStateError: If processor is not initialized
            ValueError: If text is empty or parameters are invalid
            TypeError: If text is not a string
        """
        if not self.is_initialized:
            raise ServiceStateError("Processor is not initialized")

        if not isinstance(text, str):
            raise TypeError("Input text must be a string")

        # Use config values if not overridden
        max_size = max_chunk_size or self._config.max_chunk_size
        chunk_overlap = overlap or self._config.chunk_overlap

        # Clean text first
        text = self.clean_text(text)

        # Split into chunks
        chunks = chunk_text(
            text, max_size=max_size, overlap=chunk_overlap, preserve_paragraphs=True
        )

        # Track metadata if provided
        if metadata is not None:
            metadata["num_chunks"] = len(chunks)
            metadata["avg_chunk_length"] = (
                sum(len(c) for c in chunks) / len(chunks) if chunks else 0
            )

        return chunks

    def validate_text(self, text: str) -> List[str]:
        """Validate text before processing.

        Args:
            text: Text to validate

        Returns:
            List of validation error messages, empty if valid

        Raises:
            TypeError: If text is not a string
        """
        if not isinstance(text, str):
            raise TypeError("Input text must be a string")

        # Run content validation
        errors = validate_content(text)

        # Add language validation if configured
        if self._config.detect_language:
            lang, confidence = detect_language(text, min_confidence=self._config.min_confidence)
            if not lang:
                errors.append("Language detection failed or confidence too low")

        return errors

    def initialize(self) -> None:
        """Initialize the processor.

        Performs text-specific initialization tasks.
        """
        super().initialize()
        self._processed_texts.clear()

    def cleanup(self) -> None:
        """Clean up processor resources.

        Performs text-specific cleanup tasks.
        """
        self._processed_texts.clear()
        super().cleanup()

    @property
    def processed_texts(self) -> List[str]:
        """Get list of processed texts.

        Returns:
            Copy of processed texts list
        """
        return self._processed_texts.copy()
