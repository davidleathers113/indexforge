"""Configuration settings for text summarization.

This module provides configuration classes for managing summarization parameters,
caching settings, and logging options. It includes:

1. Summarizer Configuration:
   - Model selection
   - Length control
   - Generation parameters
   - Performance settings
   - Device management

2. Cache Configuration:
   - Redis connection settings
   - TTL management
   - Key prefixing
   - Retry settings

3. Logging Configuration:
   - Log level control
   - Format customization
   - Output management
   - File handling

Usage:
    ```python
    from src.utils.summarizer.config.settings import (
        SummarizerConfig,
        CacheConfig,
        LoggingConfig
    )

    # Configure summarizer
    summarizer_config = SummarizerConfig(
        model_name="t5-small",
        max_length=150,
        min_length=50,
        temperature=0.7
    )

    # Configure caching
    cache_config = CacheConfig(
        enabled=True,
        host="localhost",
        port=6379,
        ttl=86400
    )

    # Configure logging
    logging_config = LoggingConfig(
        level="INFO",
        file_path="/path/to/logs/summarizer.log"
    )
    ```

Note:
    - All configurations use dataclasses
    - Provides sensible defaults
    - Supports type checking
    - Includes validation
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SummarizerConfig:
    """Configuration for text summarization.

    Attributes:
        model_name: Name of the transformer model to use
        max_length: Maximum length of generated summary
        min_length: Minimum length of generated summary
        min_word_count: Minimum word count for text to summarize
        do_sample: Whether to use sampling for generation
        temperature: Sampling temperature (higher = more random)
        top_p: Nucleus sampling parameter
        chunk_size: Size of text chunks for processing
        chunk_overlap: Overlap between consecutive chunks
        device: Device to use for model (cpu/cuda)
        num_beams: Number of beams for beam search
        early_stopping: Whether to use early stopping
        no_repeat_ngram_size: Size of n-grams to avoid repeating
        length_penalty: Penalty for longer sequences
        max_time: Maximum time in seconds for generation
        skip_special_tokens: Whether to skip special tokens in output
    """

    model_name: str = "t5-small"
    max_length: int = 150
    min_length: int = 20
    min_word_count: int = 30
    do_sample: bool = False
    temperature: float = 0.7
    top_p: float = 0.9
    chunk_size: int = 512
    chunk_overlap: int = 50
    device: str = "cpu"
    num_beams: int = 4
    early_stopping: bool = True
    no_repeat_ngram_size: int = 3
    length_penalty: float = 2.0
    max_time: int = 60
    skip_special_tokens: bool = True


@dataclass
class CacheConfig:
    """Configuration for caching.

    Attributes:
        enabled: Whether caching is enabled
        host: Redis host address
        port: Redis port number
        prefix: Prefix for cache keys
        ttl: Time-to-live in seconds for cache entries
        max_attempts: Maximum retry attempts for cache operations
    """

    enabled: bool = True
    host: str = "localhost"
    port: int = 6379
    prefix: str = "summary_cache"
    ttl: int = 86400  # 24 hours
    max_attempts: int = 3


@dataclass
class LoggingConfig:
    """Configuration for logging.

    Attributes:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Log message format string
        file_path: Optional path to log file
    """

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
