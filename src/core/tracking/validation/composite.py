"""Composite validation strategy for document lineage.

This module provides a composite validator that combines multiple validation strategies
to perform comprehensive validation of document lineage data. It orchestrates the
execution of individual validators and aggregates their results.

Example:
    ```python
    validator = CompositeValidator([
        CircularDependencyValidator(),
        ChunkReferenceValidator(),
        RelationshipValidator()
    ])
    errors = validator.validate(document_lineage)
    if errors:
        print("Found validation errors:", errors)
    ```
"""

from collections.abc import Sequence
from logging import getLogger

from src.core.models import DocumentLineage
from src.core.tracking.validation.interface import ValidationStrategy
from src.core.tracking.validation.strategies.chunks import ChunkReferenceValidator
from src.core.tracking.validation.strategies.circular import CircularDependencyValidator
from src.core.tracking.validation.strategies.relationships import RelationshipValidator


logger = getLogger(__name__)


class CompositeValidator(ValidationStrategy):
    """Combines multiple validation strategies into a single validator.

    This validator orchestrates the execution of multiple validation strategies and
    aggregates their results. It provides a unified interface for validating document
    lineage data using different validation rules.

    Attributes:
        strategies: List of validation strategies to execute.
    """

    def __init__(self, strategies: Sequence[ValidationStrategy] = None) -> None:
        """Initialize the composite validator with validation strategies.

        Args:
            strategies: Optional sequence of validation strategies to use.
                If None, no strategies will be included initially.
        """
        self.strategies = list(strategies) if strategies else []

    def add_strategy(self, strategy: ValidationStrategy) -> None:
        """Add a validation strategy to the composite validator.

        Args:
            strategy: The validation strategy to add.
        """
        if not isinstance(strategy, ValidationStrategy):
            raise TypeError("Strategy must implement ValidationStrategy interface")
        self.strategies.append(strategy)

    def remove_strategy(self, strategy: ValidationStrategy) -> None:
        """Remove a validation strategy from the composite validator.

        Args:
            strategy: The validation strategy to remove.

        Raises:
            ValueError: If the strategy is not found in the validator.
        """
        try:
            self.strategies.remove(strategy)
        except ValueError:
            raise ValueError("Strategy not found in validator")

    def validate(self, lineage: DocumentLineage) -> list[str]:
        """Validate document lineage using all registered strategies.

        This method executes each validation strategy in sequence and combines
        their error messages into a single list.

        Args:
            lineage: The document lineage data to validate.

        Returns:
            A list of error messages from all validation strategies.
        """
        if not lineage:
            return []

        errors: list[str] = []

        for strategy in self.strategies:
            try:
                strategy_errors = strategy.validate(lineage)
                if strategy_errors:
                    logger.info(
                        f"Validator {strategy.__class__.__name__} found {len(strategy_errors)} errors"
                    )
                    errors.extend(strategy_errors)
            except Exception as e:
                logger.error(f"Error in validator {strategy.__class__.__name__}: {e!s}")
                errors.append(f"Validation error in {strategy.__class__.__name__}: {e!s}")

        if errors:
            logger.warning(f"Found {len(errors)} total validation errors")

        return errors

    @classmethod
    def create_default(cls) -> "CompositeValidator":
        """Create a composite validator with default validation strategies.

        This method creates a new composite validator pre-configured with the standard
        set of validation strategies:
        - CircularDependencyValidator
        - ChunkReferenceValidator
        - RelationshipValidator

        Returns:
            A new CompositeValidator instance with default strategies.
        """
        return cls(
            [CircularDependencyValidator(), ChunkReferenceValidator(), RelationshipValidator()]
        )
