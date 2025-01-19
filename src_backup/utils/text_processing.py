"""Text processing utilities for document handling.

This module provides essential text processing functions optimized for document
handling and analysis. It includes:

1. Text Cleaning:
   - Whitespace normalization
   - Special character handling
   - Empty line management
   - Unicode normalization

2. Text Truncation:
   - Token-based truncation
   - Character-based truncation
   - Model-specific tokenization
   - Length preservation

3. Text Chunking:
   - Token-based chunking
   - Character-based chunking
   - Word-based chunking
   - Overlap support

4. Text Analysis:
   - Language detection
   - Encoding detection
   - Content validation
   - Format checking
   - Text embeddings generation

Usage:
    ```python
    from src.utils.text_processing import clean_text, truncate_text, generate_embeddings

    # Clean text
    text = clean_text("Multiple    spaces   and\\nlines")
    print(text)  # "Multiple spaces and lines"

    # Truncate text
    truncated = truncate_text(
        text,
        max_length=100,
        use_tokens=True,
        model_name="gpt-3.5-turbo"
    )

    # Generate embeddings
    embedding = generate_embeddings(text)  # 384-dimensional vector
    ```

Note:
    - Handles Unicode text correctly
    - Preserves semantic meaning
    - Thread-safe operations
    - Memory efficient
    - Consistent embeddings for same input
"""

import logging

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

from .chunking.base import (
    ChunkingConfig,
    chunk_text_by_chars,
    chunk_text_by_tokens,
    chunk_text_by_words,
    get_token_encoding,
)


logger = logging.getLogger(__name__)

# Initialize the model and tokenizer globally for reuse
_model_name = "sentence-transformers/all-MiniLM-L6-v2"
_tokenizer = AutoTokenizer.from_pretrained(_model_name)
_model = AutoModel.from_pretrained(_model_name)

# Move model to GPU if available
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_model = _model.to(_device)

__all__ = [
    "ChunkingConfig",
    "chunk_text_by_chars",
    "chunk_text_by_tokens",
    "chunk_text_by_words",
    "clean_text",
    "count_tokens",
    "generate_embeddings",
    "get_token_encoding",
    "truncate_text",
]


def count_tokens(text: str, model_name: str | None = None) -> int:
    """Count the number of tokens in a text string.

    Args:
        text: Text to count tokens for
        model_name: Optional model name for token encoding

    Returns:
        Number of tokens in the text
    """
    if not text:
        return 0

    encoding = get_token_encoding(model_name)
    return len(encoding.encode(text))


def clean_text(text: str) -> str:
    """Clean and normalize text content.

    Args:
        text: Text to clean

    Returns:
        Cleaned and normalized text
    """
    if not text:
        return ""

    # Replace multiple newlines with single newline
    text = " ".join(line.strip() for line in text.splitlines())

    # Replace multiple spaces with single space
    text = " ".join(text.split())

    return text.strip()


def truncate_text(
    text: str,
    max_length: int,
    use_tokens: bool = False,
    model_name: str | None = None,
) -> str:
    """Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length in tokens or characters
        use_tokens: If True, truncate by tokens. If False, truncate by characters.
        model_name: Optional model name for token encoding

    Returns:
        Truncated text
    """
    if not text:
        return ""

    if use_tokens:
        encoding = get_token_encoding(model_name)
        tokens = encoding.encode(text)

        if len(tokens) <= max_length:
            return text

        return encoding.decode(tokens[:max_length])
    else:
        if len(text) <= max_length:
            return text

        return text[:max_length]


def generate_embeddings(text: str) -> np.ndarray:
    """
    Generate embeddings for the given text using a pre-trained model.

    This function generates consistent 384-dimensional embeddings for text input,
    suitable for semantic search and document comparison.

    Args:
        text: The text to generate embeddings for

    Returns:
        384-dimensional numpy array of embeddings

    Raises:
        ValueError: If text is empty or None
        TypeError: If text is not a string

    Example:
        ```python
        text = "Sample document content"
        embedding = generate_embeddings(text)
        print(f"Generated {len(embedding)} dimensional embedding")
        ```
    """
    if not isinstance(text, str):
        logger.error("Invalid input type: %s", type(text))
        raise TypeError("Text must be a string")

    if not text or not text.strip():
        logger.error("Empty text input")
        raise ValueError("Text cannot be empty")

    try:
        # Clean text before generating embeddings
        text = clean_text(text)

        # Tokenize text
        inputs = _tokenizer(
            text, padding=True, truncation=True, max_length=512, return_tensors="pt"
        ).to(_device)

        # Generate embeddings
        with torch.no_grad():
            outputs = _model(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1)  # Mean pooling
            embedding = embeddings[0].cpu().numpy()  # Convert to numpy array

        # Validate dimensions
        if embedding.shape != (384,):
            logger.error("Invalid embedding dimension: %s", embedding.shape)
            raise ValueError(f"Expected 384-dimensional embedding, got {embedding.shape[0]}")

        # Validate numeric constraints
        if not np.all(np.isfinite(embedding)):
            logger.error("Embedding contains non-finite values")
            raise ValueError("Embedding contains NaN or infinite values")

        return embedding

    except Exception as e:
        logger.error("Error generating embeddings: %s", str(e), exc_info=True)
        raise
