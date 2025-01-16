"""Utility package for document processing operations.

This package provides various utility modules and functions used throughout the
document processing pipeline. It includes tools for text summarization, topic
clustering, PII detection, and other document processing operations.

Modules:
    summarizer: Module for generating document summaries using various algorithms

Example:
    ```python
    from src.utils import summarizer

    # Create a summarizer instance
    doc_summarizer = summarizer.DocumentSummarizer()

    # Generate a summary
    text = "Long document text..."
    summary = doc_summarizer.summarize(
        text,
        max_length=150,
        min_length=50
    )
    ```

Note:
    Each utility module is designed to be independent and reusable, following
    the single responsibility principle.
"""

from . import summarizer


__all__ = ["summarizer"]
