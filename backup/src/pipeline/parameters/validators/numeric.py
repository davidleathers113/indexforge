"""Numeric value validator implementation."""

from typing import Optional, Union

from src.pipeline.errors import ValidationError
from src.pipeline.parameters.validators.base import Validator


class NumericValidator(Validator):
    """Validator for numeric values."""

    def __init__(
        self,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
    ):
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value: Union[int, float, str], param_name: str) -> None:
        """Validate a numeric value.

        Args:
            value: Value to validate
            param_name: Name of the parameter being validated

        Raises:
            ValidationError: If validation fails
        """
        try:
            if isinstance(value, str):
                value = float(value.strip())
            if not isinstance(value, (int, float)):
                raise ValidationError(f"{param_name} must be numeric, got {type(value).__name__}")

            if self.min_value is not None and value < self.min_value:
                raise ValidationError(
                    f"{param_name} must be greater than or equal to {self.min_value}"
                )

            if self.max_value is not None and value > self.max_value:
                raise ValidationError(
                    f"{param_name} must be less than or equal to {self.max_value}"
                )

        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid numeric value for {param_name}: {str(e)}")
