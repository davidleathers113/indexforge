"""Configuration module for text summarization.

This module provides configuration classes for managing summarization settings,
including model parameters, caching options, and logging preferences. It includes:

1. Configuration Types:
   - Summarizer settings
   - Cache settings
   - Logging settings

2. Features:
   - Type validation
   - Default values
   - Documentation
   - Extensibility

3. Integration:
   - Pipeline configuration
   - Cache management
   - Logging setup
   - Error handling

Usage:
    ```python
    from src.utils.summarizer.config import (
        SummarizerConfig,
        CacheConfig,
        LoggingConfig
    )

    # Configure components
    summarizer_config = SummarizerConfig(
        model_name="t5-small",
        max_length=150
    )
    cache_config = CacheConfig(enabled=True)
    logging_config = LoggingConfig(level="INFO")
    ```

Note:
    - Uses dataclasses for type safety
    - Provides sensible defaults
    - Supports validation
    - Enables customization
"""

from .settings import CacheConfig, LoggingConfig, SummarizerConfig

__all__ = ["CacheConfig", "LoggingConfig", "SummarizerConfig"]
