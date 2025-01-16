"""Base text chunking functions for Weaviate integration.

This module provides fundamental text chunking functions optimized for Weaviate:

1. Token-based Chunking:
   - Model-specific token counting
   - Configurable chunk sizes and overlap
   - Support for various tokenizers

2. Character-based Chunking:
   - Simple character-level segmentation
   - Fixed or variable chunk sizes
   - Configurable overlap

3. Word-based Chunking:
   - Natural word boundary preservation
   - Configurable chunk sizes
   - Overlap control

The module uses tiktoken for token counting and encoding, supporting various
models including OpenAI's GPT series and other compatible tokenizers.

Usage:
    ```python
    # Token-based chunking (recommended for embeddings)
    config = ChunkingConfig(chunk_size=512, model_name="text-embedding-3-small")
    chunks = chunk_text_by_tokens(text, config)

    # Character-based chunking
    chunks = chunk_text_by_chars(text, chunk_size=1000, overlap=100)

    # Word-based chunking
    chunks = chunk_text_by_words(text, chunk_size=100, overlap=10)
    ```

References:
    - Weaviate Chunking Guide: https://weaviate.io/developers/academy/chunking
    - Token Counting: https://weaviate.io/developers/weaviate/config-refs/tokenization
"""

from dataclasses import dataclass, field
import logging
from uuid import UUID, uuid4

import tiktoken


logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a chunk of text with metadata.

    Attributes:
        id: Unique identifier for the chunk
        content: The text content of the chunk
        metadata: Optional metadata about the chunk
    """

    id: UUID
    content: str
    metadata: dict | None = None

    def __post_init__(self):
        """Initialize default values after creation."""
        if self.id is None:
            object.__setattr__(self, "id", uuid4())
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})


@dataclass(frozen=True)
class ChunkingConfig:
    """Configuration for text chunking.

    Attributes:
        chunk_size: Size of each chunk in tokens
        chunk_overlap: Number of overlapping tokens between chunks
        model_name: Name of the model to use for tokenization
        use_advanced_chunking: Whether to use advanced chunking features
        min_chunk_size: Minimum chunk size in tokens
        max_chunk_size: Maximum chunk size in tokens
    """

    chunk_size: int = 512
    chunk_overlap: int = 50
    model_name: str = "cl100k_base"
    use_advanced_chunking: bool = False
    min_chunk_size: int = 25
    max_chunk_size: int = 100

    # Private field to store the token encoder
    _encoder: tiktoken.Encoding | None = field(init=False, repr=False, default=None)

    def __post_init__(self):
        """Initialize the encoder after creation."""
        try:
            # Initialize the encoder
            object.__setattr__(self, "_encoder", get_token_encoding(self.model_name))
        except Exception as e:
            # Log error but don't fail initialization - will try again when needed
            logger.warning(f"Failed to initialize encoder: {e!s}")
            object.__setattr__(self, "_encoder", None)

    def get_encoder(self) -> tiktoken.Encoding:
        """Get the token encoder, initializing it if necessary.

        Returns:
            The token encoder for this configuration

        Raises:
            ValueError: If encoder initialization fails
        """
        if self._encoder is None:
            object.__setattr__(self, "_encoder", get_token_encoding(self.model_name))
        return self._encoder

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string.

        Args:
            text: The text to count tokens for

        Returns:
            The number of tokens in the text

        Note:
            Uses the specified model's tokenizer if model_name is set,
            otherwise falls back to the default cl100k_base encoding.
        """
        if self._encoder is None:
            if self.model_name:
                object.__setattr__(self, "_encoder", tiktoken.encoding_for_model(self.model_name))
            else:
                object.__setattr__(self, "_encoder", tiktoken.get_encoding("cl100k_base"))
        return len(self._encoder.encode(text))

    def __str__(self) -> str:
        """Return a human-readable string representation of the configuration."""
        params = [
            f"chunk_size={self.chunk_size}",
            f"chunk_overlap={self.chunk_overlap}",
            f"use_advanced_chunking={self.use_advanced_chunking}",
            f"min_chunk_size={self.min_chunk_size}",
            f"max_chunk_size={self.max_chunk_size}",
        ]
        if self.model_name:
            params.append(f"model_name='{self.model_name}'")
        return f"ChunkingConfig({', '.join(params)})"

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging."""
        return self.__str__()


def get_token_encoding(model_name: str | None = None) -> tiktoken.Encoding:
    """Get the appropriate token encoding for a model.

    Args:
        model_name: Optional name of the model to get encoding for

    Returns:
        The appropriate token encoding for the model

    Raises:
        ValueError: If the model name is invalid or encoding initialization fails
    """
    try:
        # Always use cl100k_base for text-embedding-3-small
        if model_name == "text-embedding-3-small" or model_name == "cl100k_base":
            return tiktoken.get_encoding("cl100k_base")
        elif model_name:
            try:
                return tiktoken.encoding_for_model(model_name)
            except KeyError:
                # If model-specific encoding fails, fall back to default
                return tiktoken.get_encoding("cl100k_base")
        return tiktoken.get_encoding("cl100k_base")  # Default encoding
    except Exception as e:
        raise ValueError(f"Failed to initialize token encoding: {e!s}") from e


def chunk_text_by_tokens(text: str, config: ChunkingConfig) -> list[str]:
    """Split text into chunks based on token count.

    Args:
        text: The text to split into chunks
        config: The chunking configuration to use

    Returns:
        A list of text chunks

    Raises:
        ValueError: If text chunking fails
    """
    if not text:
        return []

    try:
        if config._encoder is None:
            tokens = get_token_encoding(config.model_name).encode(text)
        else:
            tokens = config._encoder.encode(text)
        chunks = []

        i = 0
        while i < len(tokens):
            # Get chunk of tokens
            chunk_end = min(i + config.chunk_size, len(tokens))
            chunk = tokens[i:chunk_end]

            # Convert back to text
            chunk_text = (
                config._encoder.decode(chunk)
                if config._encoder
                else get_token_encoding(config.model_name).decode(chunk)
            )
            chunks.append(chunk_text)

            # Move forward by chunk_size - overlap
            i += config.chunk_size - config.chunk_overlap

        return chunks
    except Exception as e:
        raise ValueError(f"Failed to chunk text: {e!s}") from e


def chunk_text_by_chars(text: str, chunk_size: int, overlap: int = 0) -> list[str]:
    """Split text into chunks based on character count.

    Args:
        text: The text to split into chunks
        chunk_size: The size of each chunk in characters
        overlap: The number of characters to overlap between chunks

    Returns:
        A list of text chunks
    """
    if not text:
        return []

    chunks = []
    i = 0
    while i < len(text):
        # Get chunk
        chunk_end = min(i + chunk_size, len(text))
        chunk = text[i:chunk_end]
        chunks.append(chunk)

        # Move forward by chunk_size - overlap
        i += chunk_size - overlap

    return chunks


def chunk_text_by_words(text: str, chunk_size: int, overlap: int = 0) -> list[str]:
    """Split text into chunks by word count.

    Args:
        text: The text to split into chunks
        chunk_size: The size of each chunk in words
        overlap: The number of words to overlap between chunks

    Returns:
        A list of text chunks
    """
    words = text.split()
    if not words:
        return []

    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap  # Move start position accounting for overlap

        # Prevent infinite loop if overlap >= chunk_size
        if overlap >= chunk_size:
            break

    return chunks
