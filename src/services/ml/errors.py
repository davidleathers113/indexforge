"""ML service error types.

This module provides a consolidated set of error types for ML services,
ensuring consistent error handling and reporting across implementations.
"""

from typing import Any, Optional

from src.core.errors import ServiceError


class MLServiceError(ServiceError):
    """Base class for ML service errors."""

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
        super().__init__(message)
        self.service_name = service_name
        self.details = details or {}


class ModelLoadError(MLServiceError):
    """Raised when model loading fails."""

    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        model_path: Optional[str] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            service_name: Name of the service
            model_path: Path to model that failed to load
            cause: Original exception causing the error
        """
        details = {
            "model_path": model_path,
            "cause": str(cause) if cause else None,
        }
        super().__init__(message, service_name, details)
        self.__cause__ = cause


class InvalidParametersError(MLServiceError):
    """Raised when model parameters are invalid."""

    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        parameter_errors: Optional[dict[str, str]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            service_name: Name of the service
            parameter_errors: Dict mapping parameter names to error messages
        """
        details = {"parameter_errors": parameter_errors or {}}
        super().__init__(message, service_name, details)


class ProcessingError(MLServiceError):
    """Raised when ML processing fails."""

    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        input_details: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            service_name: Name of the service
            input_details: Details about the input that caused the error
            cause: Original exception causing the error
        """
        details = {
            "input_details": input_details or {},
            "cause": str(cause) if cause else None,
        }
        super().__init__(message, service_name, details)
        self.__cause__ = cause


class ResourceExhaustedError(MLServiceError):
    """Raised when service resources are exhausted."""

    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        resource_limits: Optional[dict[str, Any]] = None,
        current_usage: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            service_name: Name of the service
            resource_limits: Dict of resource limits
            current_usage: Dict of current resource usage
        """
        details = {
            "resource_limits": resource_limits or {},
            "current_usage": current_usage or {},
        }
        super().__init__(message, service_name, details)
