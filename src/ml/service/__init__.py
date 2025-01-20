"""ML service package.

This package provides service-related functionality for ML components,
including state management, validation, and error handling.
"""

from .base import BaseService, ServiceProtocol
from .errors import (
    ServiceError,
    ServiceInitializationError,
    ServiceNotInitializedError,
    ServiceStateError,
)
from .state import ServiceState, StateManager
from .validation.base import CompositeValidator, ValidationStrategy, Validator

__all__ = [
    # Base service
    "BaseService",
    "ServiceProtocol",
    # State management
    "ServiceState",
    "StateManager",
    # Error types
    "ServiceError",
    "ServiceStateError",
    "ServiceInitializationError",
    "ServiceNotInitializedError",
    # Validation
    "Validator",
    "ValidationStrategy",
    "CompositeValidator",
]

# Version information
__version__ = "1.0.0"
