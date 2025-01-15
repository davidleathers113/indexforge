"""Text processing module.

This module provides functionality for processing and normalizing text data.
"""

import re
from enum import Enum
from typing import TYPE_CHECKING, List

try:
    import nltk
    from nltk.tokenize import sent_tokenize

    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

from src.core import BaseService, ServiceStateError
from src.core import TextProcessor as TextProcessorInterface

if TYPE_CHECKING:
    from src.core.settings import Settings


class ServiceState(Enum):
    """Service lifecycle states."""

    CREATED = "created"
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class ServiceInitializationError(ServiceStateError):
    """Raised when service initialization fails."""

    pass


class ServiceNotInitializedError(ServiceStateError):
    """Raised when attempting to use an uninitialized service."""

    pass


class TextProcessor(BaseService, TextProcessorInterface):
    """Handles text processing and normalization operations."""

    def __init__(self, settings: "Settings"):
        """Initialize the text processor.

        Args:
            settings: Application settings
        """
        BaseService.__init__(self)
        TextProcessorInterface.__init__(self, settings)
        if not NLTK_AVAILABLE:
            raise ImportError("NLTK is required for text processing")
        self._settings = settings

    async def initialize(self) -> None:
        """Initialize NLTK resources.

        Raises:
            ServiceInitializationError: If NLTK resource download fails
        """
        self._transition_state(ServiceState.INITIALIZING)
        try:
            try:
                nltk.data.find("tokenizers/punkt")
            except LookupError:
                nltk.download("punkt", quiet=True)
            self._initialized = True
            self._transition_state(ServiceState.RUNNING)
        except Exception as e:
            self._transition_state(ServiceState.ERROR)
            raise ServiceInitializationError(
                f"Failed to initialize NLTK resources: {str(e)}"
            ) from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._transition_state(ServiceState.STOPPING)
        try:
            self._initialized = False
            self._transition_state(ServiceState.STOPPED)
        except Exception as e:
            self._transition_state(ServiceState.ERROR)
            raise ServiceStateError(f"Failed to cleanup resources: {str(e)}") from e

    def clean_text(self, text: str) -> str:
        """Clean and normalize text.

        Args:
            text: Input text to clean

        Returns:
            Cleaned text

        Raises:
            ServiceNotInitializedError: If service is not initialized
        """
        self._check_running()

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        text = text.strip()

        # Normalize quotes and dashes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace("–", "-").replace("—", "-")

        return text

    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences.

        Args:
            text: Input text to split

        Returns:
            List of sentences

        Raises:
            ServiceNotInitializedError: If service is not initialized
        """
        self._check_running()
        return sent_tokenize(text)

    def chunk_text(self, text: str, max_chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks.

        Args:
            text: Input text to chunk
            max_chunk_size: Maximum size of each chunk
            overlap: Number of characters to overlap between chunks

        Returns:
            List of text chunks

        Raises:
            ServiceNotInitializedError: If service is not initialized
        """
        self._check_running()

        # Clean text first
        text = self.clean_text(text)

        # Split into sentences
        sentences = self.split_into_sentences(text)

        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            if current_size + sentence_size > max_chunk_size and current_chunk:
                # Add current chunk to results
                chunks.append(" ".join(current_chunk))

                # Start new chunk with overlap
                overlap_size = 0
                overlap_chunk = []

                for prev_sentence in reversed(current_chunk):
                    if overlap_size + len(prev_sentence) > overlap:
                        break
                    overlap_chunk.insert(0, prev_sentence)
                    overlap_size += len(prev_sentence)

                current_chunk = overlap_chunk
                current_size = overlap_size

            current_chunk.append(sentence)
            current_size += sentence_size

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks
