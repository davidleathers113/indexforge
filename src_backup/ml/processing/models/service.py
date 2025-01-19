"""Service model definitions for text processing."""

from src.core.errors import (
    ServiceInitializationError,
    ServiceNotInitializedError,
    ServiceState,
    ServiceStateError,
)


# Re-export for backward compatibility
__all__ = [
    "ServiceInitializationError",
    "ServiceNotInitializedError",
    "ServiceState",
    "ServiceStateError",
]
