"""
Vector embedding validation for document schema compliance.

This module provides functionality to validate vector embeddings, ensuring they
meet the required dimensionality and numeric constraints for use in the vector
search system.

Key Features:
    - Dimension validation (384-dim requirement)
    - Numeric type validation
    - Value range validation
    - NaN/Infinity checks
    - Array type validation

Example:
    ```python
    from typing import List

    # Validate an embedding vector
    embedding = [0.1] * 384  # 384-dimensional vector

    try:
        validate_embedding(embedding)
        print("Embedding is valid")
    except (ValueError, TypeError) as e:
        print(f"Validation error: {e}")
    ```
"""

import logging
from typing import List, Sequence, Union

import numpy as np

logger = logging.getLogger(__name__)

# Required embedding dimension
EMBEDDING_DIM = 384


def validate_embedding(embedding: Union[List[float], Sequence[float], np.ndarray]) -> None:
    """
    Validate vector embedding dimensions and values.

    This function performs comprehensive validation of embedding vectors:
    - Validates array type (list, tuple, numpy array)
    - Checks dimension (must be exactly 384)
    - Verifies numeric types (float, int)
    - Validates value ranges (no NaN/Infinity)

    Args:
        embedding: The embedding vector to validate. Can be:
            - Python list/tuple of floats
            - Numpy array of floats
            - Any sequence of numeric values

    Raises:
        TypeError: If embedding is not a valid numeric array
        ValueError: If embedding dimensions are incorrect (not 384)
        ValueError: If embedding contains invalid values (NaN/Infinity)
        TypeError: If embedding values are not numeric

    Example:
        ```python
        # Valid embedding
        embedding = [0.1] * 384
        validate_embedding(embedding)  # Passes

        # Wrong dimension
        embedding = [0.1] * 100
        validate_embedding(embedding)  # Raises ValueError

        # Invalid values
        embedding = [0.1] * 383 + [float('nan')]
        validate_embedding(embedding)  # Raises ValueError
        ```
    """
    logger.debug("Starting embedding validation")

    # Validate input type
    if not isinstance(embedding, (list, tuple, np.ndarray)):
        logger.error(
            "Invalid embedding type: %s. Expected list, tuple, or numpy.ndarray", type(embedding)
        )
        raise TypeError("embedding.*numeric_array")

    # Convert to numpy array for efficient validation
    try:
        if not isinstance(embedding, np.ndarray):
            embedding = np.array(embedding, dtype=np.float64)
    except (ValueError, TypeError) as e:
        logger.error("Failed to convert embedding to numeric array: %s", str(e))
        raise TypeError("embedding.*numeric")

    # Validate dimension
    embedding_len = len(embedding)
    if embedding_len != EMBEDDING_DIM:
        logger.error("Invalid embedding dimension: %d. Expected %d", embedding_len, EMBEDDING_DIM)
        raise ValueError("embedding.*dimension")

    # Validate numeric types
    if not np.issubdtype(embedding.dtype, np.number):
        logger.error("Embedding contains non-numeric values: %s", embedding.dtype)
        raise TypeError("embedding.*numeric")

    # Check for NaN/Infinity
    if not np.all(np.isfinite(embedding)):
        invalid_indices = np.where(~np.isfinite(embedding))[0]
        logger.error("Embedding contains NaN or Infinity at indices: %s", invalid_indices.tolist())
        raise ValueError("embedding.*invalid_values")

    logger.info("Embedding validation successful")


def validate_embedding_batch(embeddings: List[List[float]]) -> None:
    """
    Validate a batch of embeddings.

    Useful for validating multiple embeddings at once, such as when
    processing a batch of documents.

    Args:
        embeddings: List of embedding vectors to validate

    Raises:
        TypeError: If any embedding is invalid
        ValueError: If any embedding has wrong dimensions
        ValueError: If batch is empty

    Example:
        ```python
        embeddings = [
            [0.1] * 384,  # Valid
            [0.2] * 384,  # Valid
            [0.3] * 100,  # Wrong dimension
        ]
        validate_embedding_batch(embeddings)  # Raises ValueError
        ```
    """
    logger.debug("Starting batch embedding validation for %d vectors", len(embeddings))

    if not embeddings:
        logger.error("Empty embedding batch")
        raise ValueError("embedding_batch.*empty")

    for i, embedding in enumerate(embeddings):
        try:
            validate_embedding(embedding)
        except (ValueError, TypeError) as e:
            logger.error("Validation failed for embedding %d: %s", i, str(e))
            raise ValueError(f"embedding[{i}].*{str(e)}")

    logger.info("Batch embedding validation successful")
