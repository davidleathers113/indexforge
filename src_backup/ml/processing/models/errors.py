"""Error definitions for text processing."""

from src.core.errors import (
    ServiceInitializationError,
    ServiceNotInitializedError,
    ServiceStateError,
    ValidationError,
)


# Re-export for backward compatibility
__all__ = [
    "ServiceInitializationError",
    "ServiceNotInitializedError",
    "ServiceStateError",
    "ValidationError",
]
