"""Text summarization package for document processing.

This package provides a comprehensive solution for text summarization using
transformer models with caching and configuration support. It includes:

1. Core Components:
   - Document processing
   - Pipeline management
   - Configuration handling
   - Cache management

2. Features:
   - Transformer-based summarization
   - Redis caching support
   - Batch processing
   - Resource management

3. Configuration:
   - Model settings
   - Cache settings
   - Logging settings
   - Performance tuning

4. Extensibility:
   - Custom pipeline support
   - Configurable caching
   - Logging customization
   - Error handling

Usage:
    ```python
    from src.utils.summarizer import (
        DocumentSummarizer,
        SummarizerConfig,
        CacheConfig
    )

    # Configure summarizer
    config = SummarizerConfig(
        model_name="t5-small",
        max_length=150,
        min_length=50
    )

    # Initialize with caching
    cache_config = CacheConfig(enabled=True)
    summarizer = DocumentSummarizer(config, cache_config)

    # Process documents
    docs = [doc1, doc2, doc3]
    results = summarizer.process_documents(docs)
    ```

Note:
    - Built on Hugging Face transformers
    - Supports Redis caching
    - Handles large documents
    - Thread-safe operations
"""

from .config.settings import CacheConfig, LoggingConfig, SummarizerConfig
from .core.processor import DocumentSummarizer


__all__ = [
    "CacheConfig",
    "DocumentSummarizer",
    "LoggingConfig",
    "SummarizerConfig",
]
