"""Base validation framework.

This module provides the core validation patterns and interfaces for the validation
framework, ensuring consistent validation behavior across the system.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, Protocol, Sequence, TypeVar

T = TypeVar("T")  # Type to validate
P = TypeVar("P")  # Validation parameters


class ValidationError(Exception):
    """Base class for validation errors."""

    def __init__(
        self,
        message: str,
        validation_type: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error message
            validation_type: Type of validation that failed
            details: Additional error details
        """
        super().__init__(message)
        self.validation_type = validation_type
        self.details = details or {}


class Validator(Protocol[T]):
    """Protocol defining the core validator interface."""

    def validate(self, value: T) -> list[str]:
        """Validate a value.

        Args:
            value: Value to validate

        Returns:
            List of validation error messages
        """
        ...


class ValidationStrategy(ABC, Generic[T, P]):
    """Base class for validation strategies.

    This class provides the foundation for implementing validation strategies,
    including error tracking and result management.
    """

    def __init__(self) -> None:
        """Initialize the validation strategy."""
        self._errors: list[str] = []

    @property
    def errors(self) -> list[str]:
        """Get validation errors."""
        return self._errors.copy()

    def clear_errors(self) -> None:
        """Clear validation errors."""
        self._errors.clear()

    @abstractmethod
    def validate(self, value: T, parameters: P) -> bool:
        """Validate a value.

        Args:
            value: Value to validate
            parameters: Validation parameters

        Returns:
            True if validation passes
        """
        pass

    def add_error(self, message: str) -> None:
        """Add validation error.

        Args:
            message: Error message
        """
        self._errors.append(message)


class CompositeValidator(Validator[T]):
    """Combines multiple validators.

    This class allows combining multiple validators into a single validator,
    executing them in sequence and aggregating their results.
    """

    def __init__(self, validators: Sequence[Validator[T]]) -> None:
        """Initialize the composite validator.

        Args:
            validators: Sequence of validators to apply
        """
        self._validators = list(validators)
        self._errors: list[str] = []

    @property
    def errors(self) -> list[str]:
        """Get all validation errors."""
        return self._errors.copy()

    def validate(self, value: T) -> list[str]:
        """Run all validators on value.

        Args:
            value: Value to validate

        Returns:
            List of validation error messages
        """
        self._errors.clear()
        for validator in self._validators:
            errors = validator.validate(value)
            if errors:
                self._errors.extend(errors)
        return self._errors

    def add_validator(self, validator: Validator[T]) -> None:
        """Add a validator.

        Args:
            validator: Validator to add
        """
        self._validators.append(validator)
