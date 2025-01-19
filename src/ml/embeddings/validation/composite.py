"""Composite validator implementation.

This module provides a composite validator that combines multiple validation
strategies into a single validator.
"""

from typing import List, Sequence

from src.core import Chunk

from .strategies import ValidationStrategy


class CompositeValidator(ValidationStrategy):
    """Combines multiple validation strategies into a single validator.

    This class implements the Composite pattern to allow treating
    individual and groups of validators uniformly.
    """

    def __init__(self, validators: Sequence[ValidationStrategy]) -> None:
        """Initialize with list of validators.

        Args:
            validators: List of validation strategies to use
        """
        self.validators = validators

    def validate(self, chunk: Chunk) -> List[str]:
        """Run all validators on the chunk.

        Args:
            chunk: The chunk to validate

        Returns:
            Combined list of validation error messages

        Raises:
            TypeError: If chunk is not of correct type
        """
        if not isinstance(chunk, Chunk):
            raise TypeError("Input must be a Chunk instance")

        errors: List[str] = []
        for validator in self.validators:
            errors.extend(validator.validate(chunk))
        return errors
