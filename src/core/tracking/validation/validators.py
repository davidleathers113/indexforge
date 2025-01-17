"""Composite validator for document lineage validation."""

from typing import List

from src.core.models import DocumentLineage
from src.core.tracking.validation.interfaces import ValidationStrategy


class CompositeValidator:
    """Composite validator that executes multiple validation strategies."""

    def __init__(self, strategies: List[ValidationStrategy]) -> None:
        """
        Initialize with list of validation strategies.

        Args:
            strategies: List of validation strategies to execute
        """
        self.strategies = strategies

    def validate(self, lineage_data: dict[str, DocumentLineage]) -> list[str]:
        """
        Execute all validation strategies and collect errors.

        Args:
            lineage_data: Dictionary mapping document IDs to their lineage data

        Returns:
            Combined list of error messages from all validation strategies
        """
        errors = []
        for strategy in self.strategies:
            errors.extend(strategy.validate(lineage_data))
        return errors

    @classmethod
    def create_default(cls) -> "CompositeValidator":
        """Create default validator with standard validation strategies."""
        from src.core.tracking.validation.strategies.chunks import ChunkReferenceValidator
        from src.core.tracking.validation.strategies.circular import CircularDependencyValidator
        from src.core.tracking.validation.strategies.relationships import RelationshipValidator

        strategies = [
            CircularDependencyValidator(),
            ChunkReferenceValidator(),
            RelationshipValidator(),
        ]
        return cls(strategies)
