"""Chunking strategy factory and configuration.

This module provides a factory for creating and configuring text chunking strategies,
with support for strategy selection, configuration management, and validation.

Example Usage:
    Basic text chunking with character-based strategy:
    >>> from src.utils.chunking.factory import ChunkingFactory, ChunkingConfig, ChunkingMethod
    >>> factory = ChunkingFactory()
    >>> config = ChunkingConfig(
    ...     method=ChunkingMethod.CHARACTER,
    ...     chunk_size=100,
    ...     overlap=20
    ... )
    >>> text = "Your input text here..."
    >>> chunks = factory.chunk_text(text, config)

    Using the factory as a context manager:
    >>> with ChunkingFactory() as factory:
    ...     config = ChunkingConfig(
    ...         method=ChunkingMethod.WORD,
    ...         chunk_size=50,
    ...         respect_boundaries=True
    ...     )
    ...     chunks = factory.chunk_text(long_text, config)

    Token-based chunking with specific model:
    >>> config = ChunkingConfig(
    ...     method=ChunkingMethod.TOKEN,
    ...     chunk_size=1000,
    ...     overlap=100,
    ...     model_name="gpt-3.5-turbo"
    ... )
    >>> chunks = factory.chunk_text(text, config)

    Using custom validation:
    >>> class CustomValidator(ChunkValidator):
    ...     def validate_chunk_size(self, size: int) -> None:
    ...         if not (100 <= size <= 2000):
    ...             raise ValueError("Chunk size must be between 100 and 2000")
    ...     def validate_overlap(self, overlap: int, chunk_size: int) -> None:
    ...         if overlap > chunk_size // 4:
    ...             raise ValueError("Overlap must not exceed 25% of chunk size")
    >>> config = ChunkingConfig(
    ...     method=ChunkingMethod.CHARACTER,
    ...     chunk_size=500,
    ...     validator=CustomValidator()
    ... )

Best Practices:
    1. Strategy Selection:
       - Use CHARACTER for byte-level control and simple text
       - Use WORD for natural language with word boundary respect
       - Use TOKEN for ML model compatibility and semantic chunking

    2. Chunk Size Guidelines:
       - CHARACTER: 100-5000 characters depending on content
       - WORD: 50-200 words for typical text
       - TOKEN: Model-specific (e.g., 1000-2000 for GPT models)

    3. Overlap Guidelines:
       - 10-20% of chunk_size for general use
       - Larger overlap (20-30%) for complex content
       - Smaller overlap (5-10%) for simple content

    4. Resource Management:
       - Use context manager for automatic cleanup
       - Clear cache manually for long-running applications
       - Reuse factory instance when possible

    5. Error Handling:
       - Always validate configuration parameters
       - Use custom validators for specific requirements
       - Handle ValueError for configuration issues
       - Handle potential exceptions in chunking process

Performance Considerations:
    - Strategy instances are cached based on configuration
    - Token-based chunking has initialization overhead
    - Large overlaps increase processing time
    - Memory usage scales with text and chunk size

Thread Safety:
    The factory is thread-safe for reading (getting strategies)
    but not for writing (clearing cache). Use separate instances
    for concurrent modifications.
"""

import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional, Type

from .strategies.base import ChunkingStrategy, ChunkValidator
from .strategies.char_based import CharacterBasedChunking
from .strategies.token_based import TokenBasedChunking, TokenEncoderFactory
from .strategies.word_based import WordBasedChunking

logger = logging.getLogger(__name__)


class ChunkingMethod(Enum):
    """Enumeration of available chunking methods.

    This enum defines the supported text chunking strategies:
    - CHARACTER: Split text based on character count
    - WORD: Split text based on word count
    - TOKEN: Split text based on token count (for ML models)

    Example:
        >>> config = ChunkingConfig(
        ...     method=ChunkingMethod.WORD,
        ...     chunk_size=100
        ... )
    """

    CHARACTER = auto()
    WORD = auto()
    TOKEN = auto()


@dataclass
class ChunkingConfig:
    """Configuration for chunking strategies.

    This class holds configuration parameters that can be applied to any chunking
    strategy, with validation and reasonable defaults.

    Attributes:
        method: The chunking method to use (CHARACTER, WORD, or TOKEN)
        chunk_size: Size of each chunk in the respective units
        overlap: Number of units to overlap between chunks (default: 0)
        respect_boundaries: Whether to respect natural boundaries (default: True)
        model_name: Name of the model for token-based chunking (default: None)
        validator: Optional validator for chunking parameters (default: None)

    Example:
        >>> config = ChunkingConfig(
        ...     method=ChunkingMethod.CHARACTER,
        ...     chunk_size=1000,
        ...     overlap=100,
        ...     respect_boundaries=True
        ... )

    Notes:
        - chunk_size must be positive
        - overlap must be non-negative and less than chunk_size
        - model_name is only used for TOKEN method
        - respect_boundaries affects different aspects based on method:
          * CHARACTER: Respect word boundaries
          * WORD: Respect sentence boundaries
          * TOKEN: Not used

    Raises:
        ValueError: If validation fails for chunk_size or overlap
    """

    method: ChunkingMethod
    chunk_size: int
    overlap: int = 0
    respect_boundaries: bool = True
    model_name: Optional[str] = None
    validator: Optional[ChunkValidator] = None

    def __post_init__(self):
        """Validate configuration parameters.

        Raises:
            ValueError: If any parameters are invalid
        """
        if self.chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        if self.overlap < 0:
            raise ValueError("Overlap must be non-negative")
        if self.overlap >= self.chunk_size:
            raise ValueError("Overlap must be less than chunk size")
        if self.method == ChunkingMethod.TOKEN and self.model_name is None:
            logger.info("No model specified for token-based chunking, using default")


class ChunkingFactory:
    """Factory for creating and managing chunking strategies.

    This factory handles strategy instantiation, configuration, and caching to
    provide efficient access to chunking strategies while maintaining proper
    configuration and initialization.

    The factory maintains a cache of strategy instances based on their
    configuration to avoid unnecessary instantiation. It also provides
    convenience methods for direct text chunking.

    Example:
        >>> factory = ChunkingFactory()
        >>> config = ChunkingConfig(
        ...     method=ChunkingMethod.WORD,
        ...     chunk_size=100
        ... )
        >>> chunks = factory.chunk_text("Some long text...", config)

    Thread Safety:
        The factory is thread-safe for reading (getting strategies) but not
        for writing (clearing cache). Use separate instances for concurrent
        modifications.

    Resource Management:
        Use the factory as a context manager for automatic cleanup:
        >>> with ChunkingFactory() as factory:
        ...     chunks = factory.chunk_text(text, config)
    """

    def __init__(self):
        """Initialize the chunking factory.

        Creates empty strategy cache and initializes the token encoder factory
        if needed for token-based chunking.
        """
        self._strategies: Dict[ChunkingMethod, Type[ChunkingStrategy]] = {
            ChunkingMethod.CHARACTER: CharacterBasedChunking,
            ChunkingMethod.WORD: WordBasedChunking,
            ChunkingMethod.TOKEN: TokenBasedChunking,
        }
        self._token_encoder_factory = TokenEncoderFactory()
        self._instances: Dict[str, ChunkingStrategy] = {}

    def _get_cache_key(self, config: ChunkingConfig) -> str:
        """Generate cache key for strategy configuration.

        Creates a unique key for caching strategy instances based on their
        configuration parameters.

        Args:
            config: Chunking configuration

        Returns:
            Cache key string incorporating relevant configuration parameters
        """
        return (
            f"{config.method.name}:"
            f"{config.respect_boundaries}:"
            f"{config.model_name or 'default'}"
        )

    def _create_strategy(self, config: ChunkingConfig) -> ChunkingStrategy:
        """Create a new strategy instance.

        Instantiates and configures a chunking strategy based on the provided
        configuration.

        Args:
            config: Chunking configuration

        Returns:
            Configured chunking strategy

        Raises:
            ValueError: If strategy creation fails or method is unknown
        """
        strategy_class = self._strategies.get(config.method)
        if not strategy_class:
            raise ValueError(f"Unknown chunking method: {config.method}")

        try:
            if config.method == ChunkingMethod.TOKEN:
                return strategy_class(
                    encoder_factory=self._token_encoder_factory, validator=config.validator
                )
            elif config.method == ChunkingMethod.CHARACTER:
                return strategy_class(
                    validator=config.validator, respect_boundaries=config.respect_boundaries
                )
            elif config.method == ChunkingMethod.WORD:
                return strategy_class(
                    validator=config.validator, respect_sentences=config.respect_boundaries
                )

        except Exception as e:
            logger.error(f"Failed to create strategy: {e!s}")
            raise ValueError(f"Strategy creation failed: {e!s}") from e

    def get_strategy(self, config: ChunkingConfig) -> ChunkingStrategy:
        """Get or create a chunking strategy.

        Returns a cached strategy instance if one exists with the same
        configuration, otherwise creates a new instance.

        Args:
            config: Chunking configuration

        Returns:
            Configured chunking strategy

        Raises:
            ValueError: If strategy creation fails

        Note:
            Strategies are cached based on method, boundary respect, and
            model name (for token-based chunking). Other parameters like
            chunk_size and overlap are handled per-call.
        """
        cache_key = self._get_cache_key(config)

        if cache_key not in self._instances:
            self._instances[cache_key] = self._create_strategy(config)

        return self._instances[cache_key]

    def chunk_text(self, text: str, config: ChunkingConfig) -> list[str]:
        """Convenience method to chunk text using specified configuration.

        This method handles strategy selection and chunking in one step,
        providing a simple interface for common use cases.

        Args:
            text: Text to chunk
            config: Chunking configuration

        Returns:
            List of text chunks

        Raises:
            ValueError: If chunking fails

        Example:
            >>> config = ChunkingConfig(
            ...     method=ChunkingMethod.WORD,
            ...     chunk_size=50,
            ...     overlap=10
            ... )
            >>> chunks = factory.chunk_text("Long text...", config)
        """
        strategy = self.get_strategy(config)
        try:
            return strategy.chunk(
                text,
                chunk_size=config.chunk_size,
                overlap=config.overlap,
                model_name=config.model_name if config.method == ChunkingMethod.TOKEN else None,
            )
        except Exception as e:
            logger.error(f"Chunking failed: {e!s}")
            raise ValueError(f"Chunking failed: {e!s}") from e

    def clear_cache(self):
        """Clear the strategy instance cache.

        This method removes all cached strategy instances, forcing new
        instances to be created on next use. Use this method to free
        memory or when strategy parameters need to be reset.
        """
        self._instances.clear()

    def __enter__(self):
        """Context manager entry.

        Returns:
            self: The factory instance
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cache cleanup.

        Cleans up resources by clearing the strategy cache when the
        context is exited.
        """
        self.clear_cache()
