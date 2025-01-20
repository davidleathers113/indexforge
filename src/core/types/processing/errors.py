"""Processing error types.

This module defines error types specific to processing operations,
providing a consistent way to handle and report processing errors.

Key Features:
    - Processing error hierarchy
    - Validation errors
    - State errors
    - Resource errors
"""

from typing import Any, Optional

from src.core.types.service import ServiceError


class ProcessingError(ServiceError):
    """Base class for processing errors."""

    def __init__(self, message: str, service_name: Optional[str] = None) -> None:
        """Initialize processing error.

        Args:
            message: Error message
            service_name: Name of service that raised the error
        """
        super().__init__(message, service_name)


class ValidationError(ProcessingError):
    """Raised when validation fails."""

    def __init__(
        self,
        message: str,
        validation_errors: list[str],
        service_name: Optional[str] = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error message
            validation_errors: List of validation error messages
            service_name: Name of service that raised the error
        """
        super().__init__(message, service_name)
        self.validation_errors = validation_errors


class ProcessingStateError(ProcessingError):
    """Raised when operation is invalid for current state."""

    def __init__(
        self,
        message: str,
        current_state: Any,
        expected_states: set[Any],
        service_name: Optional[str] = None,
    ) -> None:
        """Initialize state error.

        Args:
            message: Error message
            current_state: Current processing state
            expected_states: Set of valid states for operation
            service_name: Name of service that raised the error
        """
        super().__init__(message, service_name)
        self.current_state = current_state
        self.expected_states = expected_states


class ResourceError(ProcessingError):
    """Raised when required resources are unavailable."""

    def __init__(
        self,
        message: str,
        resource_type: str,
        resource_id: str,
        service_name: Optional[str] = None,
    ) -> None:
        """Initialize resource error.

        Args:
            message: Error message
            resource_type: Type of resource that was unavailable
            resource_id: ID of resource that was unavailable
            service_name: Name of service that raised the error
        """
        super().__init__(message, service_name)
        self.resource_type = resource_type
        self.resource_id = resource_id


class ProcessingTimeout(ProcessingError):
    """Raised when processing operation times out."""

    def __init__(
        self,
        message: str,
        timeout_seconds: float,
        operation: str,
        service_name: Optional[str] = None,
    ) -> None:
        """Initialize timeout error.

        Args:
            message: Error message
            timeout_seconds: Timeout duration in seconds
            operation: Name of operation that timed out
            service_name: Name of service that raised the error
        """
        super().__init__(message, service_name)
        self.timeout_seconds = timeout_seconds
        self.operation = operation
