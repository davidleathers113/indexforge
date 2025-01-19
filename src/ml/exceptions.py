"""ML utilities exceptions.

This module defines custom exceptions for ML utilities to provide more specific
error handling and better error messages.
"""


class MLUtilsError(Exception):
    """Base exception for all ML utilities errors."""

    pass


class EmbeddingError(MLUtilsError):
    """Errors related to embedding generation and manipulation.

    Examples:
        - Model initialization failures
        - Input validation errors
        - Batch processing errors
    """

    pass


class ModelInitError(EmbeddingError):
    """Error initializing ML models."""

    pass


class InputValidationError(EmbeddingError):
    """Error validating input data."""

    pass


class ClusteringError(MLUtilsError):
    """Errors related to document clustering and topic analysis.

    Examples:
        - Insufficient data for clustering
        - Invalid cluster configuration
        - Silhouette analysis failures
    """

    pass


class InsufficientDataError(ClusteringError):
    """Error when not enough data is available for operation."""

    pass


class ConfigurationError(ClusteringError):
    """Error in clustering configuration."""

    pass


class VectorIndexError(MLUtilsError):
    """Errors related to vector indexing and similarity search.

    Examples:
        - Index initialization failures
        - Vector dimension mismatches
        - GPU resource errors
    """

    pass


class ResourceError(VectorIndexError):
    """Error managing hardware resources (CPU/GPU)."""

    pass


class DimensionMismatchError(VectorIndexError):
    """Error when vector dimensions don't match."""

    pass
