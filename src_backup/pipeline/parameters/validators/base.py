"""Base validator implementation."""

from abc import ABC, abstractmethod
from typing import Any

from src.pipeline.errors import ValidationError


class Validator(ABC):
    """Base class for all validators."""

    @abstractmethod
    def validate(self, value: Any, param_name: str) -> None:
        """Validate a value.

        Args:
            value: Value to validate
            param_name: Name of the parameter being validated

        Raises:
            ValidationError: If validation fails
        """
        pass


class CompositeValidator(Validator):
    """Validator that combines multiple validators."""

    def __init__(self, validators: list[Validator] | None = None):
        self.validators = validators or []

    def add_validator(self, validator: Validator) -> None:
        """Add a validator to the composite."""
        self.validators.append(validator)

    def validate(self, value: Any, param_name: str) -> None:
        """Run all validators on the value."""
        errors = []
        for validator in self.validators:
            try:
                validator.validate(value, param_name)
            except ValidationError as e:
                errors.append(str(e))
        if errors:
            raise ValidationError(
                f"Multiple validation errors for {param_name}:\n" + "\n".join(errors)
            )
