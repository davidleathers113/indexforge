"""Base classes for chunk validation strategies."""

from abc import ABC, abstractmethod

from src.ml.processing.models.chunks import Chunk


class ValidationStrategy(ABC):
    """Base class for chunk validation strategies.

    This class defines the interface for all validation strategies.
    Each concrete strategy implements specific validation logic.
    """

    @abstractmethod
    def validate(self, chunk: Chunk, metadata: dict | None = None) -> list[str]:
        """Validate a chunk using this strategy.

        Args:
            chunk: The chunk to validate
            metadata: Optional metadata to use in validation

        Returns:
            List of validation error messages, empty if valid
        """
        pass


class CompositeValidator(ValidationStrategy):
    """Combines multiple validation strategies into one.

    This class implements the Composite pattern to allow treating
    individual and groups of validators uniformly.
    """

    def __init__(self, validators: list[ValidationStrategy]) -> None:
        """Initialize with list of validators.

        Args:
            validators: List of validation strategies to use
        """
        self.validators = validators

    def validate(self, chunk: Chunk, metadata: dict | None = None) -> list[str]:
        """Run all validators on the chunk.

        Args:
            chunk: The chunk to validate
            metadata: Optional metadata to use in validation

        Returns:
            Combined list of validation error messages
        """
        errors = []
        for validator in self.validators:
            errors.extend(validator.validate(chunk, metadata))
        return errors


class ValidatorBuilder:
    """Builder for constructing validation chains.

    This class implements the Builder pattern to allow flexible
    construction of validator combinations.
    """

    def __init__(self) -> None:
        """Initialize an empty validator builder."""
        self.validators: list[ValidationStrategy] = []

    def add_validator(self, validator: ValidationStrategy) -> "ValidatorBuilder":
        """Add a validator to the chain.

        Args:
            validator: Validation strategy to add

        Returns:
            Self for method chaining
        """
        self.validators.append(validator)
        return self

    def build(self) -> ValidationStrategy:
        """Build the final validator.

        Returns:
            A composite validator containing all added strategies
        """
        return CompositeValidator(self.validators)
