"""Base validation functionality for ML services.

This module provides the foundation for service validation, including
protocols and base classes for implementing validation strategies.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, Protocol, Sequence, TypeVar

T = TypeVar("T")
P = TypeVar("P")


class Validator(Protocol[T]):
    """Protocol for validators."""

    def validate(self, value: T) -> list[str]:
        """Validate a value.

        Args:
            value: Value to validate

        Returns:
            List of validation error messages
        """
        ...


class ValidationStrategy(ABC, Generic[T]):
    """Base class for validation strategies.

    Provides:
    - Core validation interface
    - Error message handling
    - Validation result management
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
    def validate(self, value: T) -> bool:
        """Validate a value.

        Args:
            value: Value to validate

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

    Provides:
    - Sequential validation
    - Aggregated error messages
    - Flexible validator composition
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
