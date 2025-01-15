"""String value validator implementation."""

import re
from typing import Optional

from src.pipeline.errors import ValidationError
from src.pipeline.parameters.validators.base import Validator


class StringValidator(Validator):
    """Validator for string values."""

    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self._compiled_pattern = re.compile(pattern) if pattern else None

    def validate(self, value: str, param_name: str) -> None:
        """Validate a string value.

        Args:
            value: Value to validate
            param_name: Name of the parameter being validated

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, (str, bytes)):
            raise ValidationError(
                f"{param_name} must be string or bytes, got {type(value).__name__}"
            )

        if isinstance(value, bytes):
            try:
                value = value.decode("utf-8")
            except UnicodeDecodeError as e:
                raise ValidationError(f"Invalid UTF-8 encoding in {param_name}: {str(e)}")

        value = value.strip()

        if self.min_length is not None and len(value) < self.min_length:
            raise ValidationError(
                f"{param_name} must be at least {self.min_length} characters long"
            )

        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationError(f"{param_name} must be at most {self.max_length} characters long")

        if self._compiled_pattern and not self._compiled_pattern.match(value):
            raise ValidationError(f"{param_name} must match pattern {self.pattern}")
