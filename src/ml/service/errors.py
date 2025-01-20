"""Service-related error types.

This module provides a consolidated set of error types for ML services,
ensuring consistent error handling and reporting.
"""

from typing import Any, Optional, Sequence


class ServiceError(Exception):
    """Base class for service-related errors."""

    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            service_name: Name of the service raising the error
            details: Additional error details
        """
        self.service_name = service_name
        self.details = details or {}
        super().__init__(message)


class ServiceStateError(ServiceError):
    """Raised when service is in invalid state for operation."""

    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        current_state: Optional[str] = None,
        required_state: Optional[str] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            service_name: Name of the service
            current_state: Current service state
            required_state: Required service state
        """
        details = {
            "current_state": current_state,
            "required_state": required_state,
        }
        super().__init__(message, service_name, details)


class ServiceInitializationError(ServiceError):
    """Raised when service initialization fails."""

    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        cause: Optional[Exception] = None,
        missing_dependencies: Optional[Sequence[str]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            service_name: Name of the service
            cause: Original exception causing the error
            missing_dependencies: List of missing dependencies
        """
        details = {
            "cause": str(cause) if cause else None,
            "missing_dependencies": list(missing_dependencies) if missing_dependencies else [],
        }
        super().__init__(message, service_name, details)
        self.__cause__ = cause


class ServiceNotInitializedError(ServiceError):
    """Raised when attempting to use uninitialized service."""

    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        required_state: Optional[str] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            service_name: Name of the service
            required_state: Required service state
        """
        details = {"required_state": required_state}
        super().__init__(message, service_name, details)
