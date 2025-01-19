"""Weaviate repository exceptions.

This module defines custom exceptions for the Weaviate repository implementation.
"""


class RepositoryError(Exception):
    """Base exception for repository errors."""

    pass


class RepositoryConfigError(RepositoryError):
    """Exception raised for repository configuration errors."""

    pass


class BatchConfigurationError(RepositoryError):
    """Exception raised for batch configuration errors."""

    pass


class BatchOperationError(RepositoryError):
    """Exception raised for batch operation errors."""

    pass
