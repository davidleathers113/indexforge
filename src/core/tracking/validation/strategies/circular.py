"""Circular dependency validation strategy."""

from typing import Set

from src.core.models import DocumentLineage
from src.core.tracking.validation.errors import LineageValidationErrorFactory
from src.core.tracking.validation.interfaces import ValidationStrategy


class CircularDependencyValidator(ValidationStrategy):
    """Validates document lineage for circular dependencies."""

    def __init__(self) -> None:
        """Initialize the validator with error factory."""
        self.error_factory = LineageValidationErrorFactory()

    def validate(self, lineage_data: dict[str, DocumentLineage]) -> list[str]:
        """
        Check for circular derivation relationships between documents.

        Args:
            lineage_data: Dictionary mapping document IDs to their lineage data

        Returns:
            List of error messages for any circular derivations found
        """
        errors = []
        visited = set()

        def check_derivation_chain(doc_id: str, chain: Set[str]) -> None:
            """Recursively check derivation chain for cycles."""
            if doc_id in chain:
                cycle = list(chain)[list(chain).index(doc_id) :] + [doc_id]
                error = self.error_factory.create_error("circular", cycle=cycle)
                errors.append(error.format_message())
                return

            if doc_id in visited:
                return

            visited.add(doc_id)
            doc = lineage_data.get(doc_id)
            if doc and doc.derived_from:
                chain.add(doc_id)
                check_derivation_chain(doc.derived_from, chain)
                chain.remove(doc_id)

        for doc_id in lineage_data:
            check_derivation_chain(doc_id, set())

        return errors
