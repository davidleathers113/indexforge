"""Service error definitions.

This module defines the core error types used across the service layer
for consistent error handling and reporting.
"""

from typing import Optional


class ServiceError(Exception):
    """Base class for all service-related errors."""

    def __init__(self, message: str, service_name: Optional[str] = None) -> None:
        """Initialize the service error.

        Args:
            message: Error description
            service_name: Optional name of the service that raised the error
        """
        self.service_name = service_name
        super().__init__(f"{service_name + ': ' if service_name else ''}{message}")


class ServiceStateError(ServiceError):
    """Raised when a service operation fails due to invalid state.

    This can occur due to:
    - Service not initialized
    - Invalid state transition
    - Connection failures
    - Resource unavailability
    - Timeout conditions
    """

    pass


class ServiceInitializationError(ServiceError):
    """Raised when service initialization fails."""

    pass


class ServiceNotInitializedError(ServiceStateError):
    """Raised when attempting to use an uninitialized service."""

    pass
