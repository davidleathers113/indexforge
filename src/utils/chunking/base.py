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

import logging
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    tiktoken = Any  # For type hints

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

    Raises:
        ValueError: If configuration parameters are invalid
        ImportError: If tiktoken is not available when tokenization is required
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
        """Initialize and validate the configuration.

        Raises:
            ValueError: If any configuration parameters are invalid
            ImportError: If tiktoken is required but not available
        """
        # Validate configuration parameters
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        if self.min_chunk_size <= 0:
            raise ValueError("min_chunk_size must be positive")
        if self.max_chunk_size < self.min_chunk_size:
            raise ValueError("max_chunk_size must be greater than or equal to min_chunk_size")
        if not isinstance(self.model_name, str):
            raise ValueError("model_name must be a string")

        if not TIKTOKEN_AVAILABLE:
            logger.warning("tiktoken not available - tokenization features will be limited")
            object.__setattr__(self, "_encoder", None)
            return

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
            ImportError: If tiktoken is not available
            ValueError: If encoder initialization fails
        """
        if not TIKTOKEN_AVAILABLE:
            raise ImportError(
                "tiktoken is required for tokenization but not installed. "
                "Install with: pip install tiktoken"
            )

        if self._encoder is None:
            object.__setattr__(self, "_encoder", get_token_encoding(self.model_name))
        return self._encoder

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string.

        Args:
            text: The text to count tokens for

        Returns:
            The number of tokens in the text

        Raises:
            ImportError: If tiktoken is not available
            ValueError: If tokenization fails
        """
        if not TIKTOKEN_AVAILABLE:
            # Fallback to simple word-based counting
            logger.warning(
                "tiktoken not available - falling back to word-based counting. "
                "This may not match model token counts exactly."
            )
            return len(text.split())

        try:
            if self._encoder is None:
                if self.model_name:
                    object.__setattr__(
                        self, "_encoder", tiktoken.encoding_for_model(self.model_name)
                    )
                else:
                    object.__setattr__(self, "_encoder", tiktoken.get_encoding("cl100k_base"))
            return len(self._encoder.encode(text))
        except Exception as e:
            logger.error(f"Failed to count tokens: {e!s}")
            raise ValueError(f"Token counting failed: {e!s}") from e

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


def chunk_text(text: str, config: "ChunkingConfig") -> list[str]:
    """Chunk text into smaller pieces based on configuration.

    Args:
        text: Text to chunk
        config: Chunking configuration

    Returns:
        List of text chunks

    Raises:
        ValueError: If text is empty or config parameters are invalid
        TypeError: If inputs are of wrong type
    """
    # Input validation
    if not isinstance(text, str):
        raise TypeError("Text must be a string")
    if not isinstance(config, ChunkingConfig):
        raise TypeError("Config must be a ChunkingConfig instance")
    if not text:
        return []

    # Validate config parameters
    if config.chunk_size <= 0:
        raise ValueError("Chunk size must be positive")
    if config.chunk_overlap < 0:
        raise ValueError("Chunk overlap cannot be negative")
    if config.chunk_overlap >= config.chunk_size:
        raise ValueError("Chunk overlap must be less than chunk size")

    chunks = []
    i = 0
    try:
        while i < len(text):
            # Calculate chunk boundaries
            chunk_end = min(i + config.chunk_size, len(text))

            # Extract chunk
            chunk = text[i:chunk_end].strip()
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)

            # Calculate next position
            i += max(1, config.chunk_size - config.chunk_overlap)

            # Safety check for infinite loops
            if i >= len(text) or (chunks and i <= len(chunks[-1])):
                break

        return chunks
    except Exception as e:
        logger.error(f"Error during text chunking: {e!s}")
        raise ValueError(f"Failed to chunk text: {e!s}") from e


# Cache for token encoders to avoid repeated initialization
_encoder_cache: dict[str, tiktoken.Encoding] = {}


def get_token_encoding(model_name: str | None = None) -> tiktoken.Encoding:
    """Get the appropriate token encoding for a model.

    This function implements caching to avoid repeated initialization of encoders.
    It also handles various model name formats and provides fallback options.

    Args:
        model_name: Optional name of the model to get encoding for

    Returns:
        The appropriate token encoding for the model

    Raises:
        ValueError: If the model name is invalid or encoding initialization fails
    """
    # Normalize model name for cache key
    cache_key = model_name or "cl100k_base"

    # Check cache first
    if cache_key in _encoder_cache:
        return _encoder_cache[cache_key]

    try:
        # Determine appropriate encoding
        if not model_name or model_name in ("text-embedding-3-small", "cl100k_base"):
            encoding = tiktoken.get_encoding("cl100k_base")
        else:
            try:
                encoding = tiktoken.encoding_for_model(model_name)
            except KeyError:
                logger.warning(f"Model {model_name} not found, falling back to cl100k_base")
                encoding = tiktoken.get_encoding("cl100k_base")

        # Cache the encoder
        _encoder_cache[cache_key] = encoding
        return encoding

    except Exception as e:
        logger.error(f"Failed to initialize token encoding for {model_name}: {e!s}")
        raise ValueError(f"Failed to initialize token encoding for {model_name}: {e!s}") from e


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
