"""Text processing module.

This module provides a comprehensive set of text processing utilities,
including cleaning, normalization, chunking, and analysis operations.
"""

from .analysis import check_format, detect_encoding, detect_language, validate_content
from .chunking import chunk_text, merge_chunks
from .cleaning import clean_text, normalize_characters, normalize_whitespace
from .config import TextProcessingConfig
from .processor import TextProcessor

__all__ = [
    # Core processor
    "TextProcessor",
    "TextProcessingConfig",
    # Cleaning operations
    "clean_text",
    "normalize_characters",
    "normalize_whitespace",
    # Chunking operations
    "chunk_text",
    "merge_chunks",
    # Analysis operations
    "detect_language",
    "detect_encoding",
    "validate_content",
    "check_format",
]
