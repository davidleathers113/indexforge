"""Weaviate error handling module for consistent error management."""

from functools import wraps
from typing import Callable, Optional, Type

import weaviate


class WeaviateError(Exception):
    """Base class for Weaviate errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        """Initialize WeaviateError.

        Args:
            message: Error message
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.original_error = original_error


class WeaviateConnectionFailure(WeaviateError):
    """Raised when connection to Weaviate fails."""

    pass


class WeaviateQueryFailure(WeaviateError):
    """Raised when a query operation fails."""

    pass


class WeaviateTimeoutFailure(WeaviateError):
    """Raised when an operation times out."""

    pass


class WeaviateAuthenticationFailure(WeaviateError):
    """Raised when authentication fails."""

    pass


def handle_weaviate_error(error: Exception) -> WeaviateError:
    """Map Weaviate client exceptions to our custom exceptions.

    Args:
        error: Original Weaviate exception

    Returns:
        WeaviateError: Mapped custom exception
    """
    error_mapping: dict[Type[Exception], Type[WeaviateError]] = {
        weaviate.exceptions.WeaviateConnectionError: WeaviateConnectionFailure,
        weaviate.exceptions.WeaviateQueryError: WeaviateQueryFailure,
        weaviate.exceptions.WeaviateTimeoutError: WeaviateTimeoutFailure,
        weaviate.exceptions.WeaviateAuthenticationError: WeaviateAuthenticationFailure,
    }

    error_class = error_mapping.get(type(error), WeaviateError)
    return error_class(str(error), original_error=error)


def with_weaviate_error_handling(func: Callable) -> Callable:
    """Decorator to handle Weaviate errors consistently.

    Args:
        func: Function to wrap with error handling

    Returns:
        Wrapped function with error handling

    Example:
        >>> @with_weaviate_error_handling
        ... def query_weaviate():
        ...     # Your code here
        ...     pass
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if isinstance(e, WeaviateError):
                raise e
            raise handle_weaviate_error(e)

    return wrapper
