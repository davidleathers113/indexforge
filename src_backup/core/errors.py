"""Core error definitions for the application.

This module provides the centralized error hierarchy for all service and processing
related errors. All other error definitions should inherit from these base classes.
"""

from collections.abc import Sequence
from enum import Enum
from typing import Any


class ServiceState(Enum):
    """Service lifecycle states.

    Defines the possible states a service can be in during its lifecycle,
    enabling proper state management and transitions.

    States:
        CREATED: Initial state after instantiation
        INITIALIZING: Service is loading resources/dependencies
        RUNNING: Service is operational and ready to process
        STOPPING: Service is cleaning up resources
        STOPPED: Service has released all resources
        ERROR: Service encountered an unrecoverable error
    """

    CREATED = "created"
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class ServiceError(Exception):
    """Base exception for all service-related errors.

    This is the root exception class for all service errors in the application.
    It provides a foundation for structured error handling and consistent
    error reporting across different service types.

    Attributes:
        message: Detailed error message
        metadata: Additional error context
    """

    def __init__(self, message: str, metadata: dict[str, Any] | None = None) -> None:
        """Initialize the error.

        Args:
            message: Detailed error message
            metadata: Additional error context
        """
        super().__init__(message)
        self.message = message
        self.metadata = metadata or {}


class ServiceStateError(ServiceError):
    """Raised when a service operation fails due to invalid state.

    This error indicates that a service operation could not be completed
    due to the current state of the service. This could be due to:
    - Service not initialized
    - Invalid state transition
    - Connection failures
    - Resource unavailability
    - Timeout conditions
    """

    pass


class ServiceInitializationError(ServiceStateError):
    """Raised when service initialization fails.

    This error indicates that a service failed to initialize properly,
    usually due to missing dependencies or invalid configuration.

    Attributes:
        message: Detailed error message
        cause: Original exception that caused the failure
        service_name: Name of the service that failed to initialize
        missing_dependencies: List of missing dependencies if applicable
    """

    def __init__(
        self,
        message: str,
        cause: Exception | None = None,
        service_name: str | None = None,
        missing_dependencies: Sequence[str] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Detailed error message
            cause: Original exception that caused the failure
            service_name: Name of the service that failed
            missing_dependencies: List of missing dependencies
        """
        super().__init__(message)
        self.cause = cause
        self.service_name = service_name
        self.missing_dependencies = missing_dependencies or []


class ServiceNotInitializedError(ServiceStateError):
    """Raised when attempting to use an uninitialized service.

    This error indicates that a service method was called before
    the service was properly initialized.

    Attributes:
        message: Detailed error message
        service_name: Name of the uninitialized service
        current_state: Current state of the service
        required_state: Required state for the operation
    """

    def __init__(
        self,
        message: str,
        service_name: str | None = None,
        current_state: str | None = None,
        required_state: str | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Detailed error message
            service_name: Name of the uninitialized service
            current_state: Current state of the service
            required_state: Required state for the operation
        """
        super().__init__(message)
        self.service_name = service_name
        self.current_state = current_state
        self.required_state = required_state


class ProcessingError(ServiceError):
    """Base class for processing-related errors.

    Provides a common base for all processing-specific errors,
    enabling consistent error handling patterns.

    Attributes:
        message: Detailed error message
        metadata: Additional error context
    """

    pass


class ValidationError(ProcessingError):
    """Raised when input validation fails.

    This error occurs when input data fails validation checks,
    providing details about the validation failures.

    Attributes:
        errors: List of validation error messages
        field_errors: Dictionary mapping fields to their errors
        validation_context: Additional context about the validation
    """

    def __init__(
        self,
        errors: Sequence[str],
        field_errors: dict[str, list[str]] | None = None,
        validation_context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            errors: List of validation error messages
            field_errors: Dictionary mapping fields to their errors
            validation_context: Additional context about the validation
        """
        super().__init__(", ".join(errors), metadata=validation_context)
        self.errors = list(errors)
        self.field_errors = field_errors or {}
        self.validation_context = validation_context or {}
