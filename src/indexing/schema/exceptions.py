"""
Custom exceptions for schema-related operations.

This module defines a hierarchy of exceptions used in schema validation,
generation, and management. These exceptions provide detailed error information
and proper error handling for schema operations.
"""

from typing import Any, Dict, List, Optional


class SchemaError(Exception):
    """Base exception for all schema-related errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the schema error.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message)
        self.details = details or {}


class SchemaValidationError(SchemaError):
    """Exception raised when schema validation fails."""

    def __init__(
        self,
        message: str,
        validation_errors: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the validation error.

        Args:
            message: Error message
            validation_errors: List of specific validation errors
            details: Additional error details
        """
        super().__init__(message, details)
        self.validation_errors = validation_errors or []


class PropertyValidationError(SchemaValidationError):
    """Exception raised when property validation fails."""

    def __init__(
        self,
        property_name: str,
        message: str,
        validation_errors: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the property validation error.

        Args:
            property_name: Name of the property that failed validation
            message: Error message
            validation_errors: List of specific validation errors
            details: Additional error details
        """
        super().__init__(
            f"Property '{property_name}' validation failed: {message}",
            validation_errors,
            details,
        )
        self.property_name = property_name


class ConfigurationError(SchemaError):
    """Exception raised when configuration validation fails."""

    def __init__(
        self,
        config_key: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the configuration error.

        Args:
            config_key: Key of the configuration that failed validation
            message: Error message
            details: Additional error details
        """
        super().__init__(
            f"Configuration '{config_key}' validation failed: {message}",
            details,
        )
        self.config_key = config_key


class ClassNameError(SchemaValidationError):
    """Exception raised when class name validation fails."""

    def __init__(
        self,
        class_name: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the class name error.

        Args:
            class_name: Invalid class name
            message: Error message
            details: Additional error details
        """
        super().__init__(
            f"Class name '{class_name}' validation failed: {message}",
            details=details,
        )
        self.class_name = class_name


class SchemaVersionError(SchemaError):
    """Exception raised when schema version validation fails."""

    def __init__(
        self,
        current_version: Optional[int],
        required_version: int,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the schema version error.

        Args:
            current_version: Current schema version
            required_version: Required schema version
            message: Optional error message
            details: Additional error details
        """
        msg = message or (
            f"Schema version mismatch: current version {current_version}, "
            f"required version {required_version}"
        )
        super().__init__(msg, details)
        self.current_version = current_version
        self.required_version = required_version
