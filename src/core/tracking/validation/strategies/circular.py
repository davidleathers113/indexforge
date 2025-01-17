"""Circular dependency validation strategy for document lineage.

This module implements validation logic to detect circular dependencies in document
lineage relationships. It checks for cycles in derivation chains and ensures that
no document can be derived from itself either directly or indirectly.

Key Features:
    - Recursive cycle detection in derivation chains
    - Self-reference validation
    - Comprehensive error reporting
    - Efficient visited node tracking
"""

import logging
from typing import Set

from src.core.models import DocumentLineage
from src.core.tracking.validation.interface import LineageValidationErrorFactory, ValidationStrategy

logger = logging.getLogger(__name__)


class CircularDependencyValidator(ValidationStrategy):
    """Validates document lineage data for circular dependencies."""

    def validate(self, lineage_data: dict[str, DocumentLineage]) -> list[str]:
        """Check for circular dependencies in document lineage.

        This method performs a depth-first search through the document derivation
        chains to detect any cycles. It tracks visited nodes to prevent infinite
        recursion and builds detailed error messages for any circular dependencies
        found.

        Args:
            lineage_data: Dictionary mapping document IDs to their lineage data

        Returns:
            List of validation error messages describing any circular dependencies

        Example:
            ```python
            validator = CircularDependencyValidator()
            errors = validator.validate({
                "doc1": DocumentLineage(id="doc1", derived_documents=["doc2"]),
                "doc2": DocumentLineage(id="doc2", derived_from="doc1")
            })
            ```
        """
        errors = []
        visited: Set[str] = set()

        def check_derivation_chain(doc_id: str, chain: Set[str]) -> None:
            """Recursively check derivation chain for cycles.

            Args:
                doc_id: Current document ID being checked
                chain: Set of document IDs in current chain
            """
            if doc_id in chain:
                # Found a cycle - create error with the cycle path
                cycle = list(chain)[list(chain).index(doc_id) :] + [doc_id]
                error = LineageValidationErrorFactory.create_circular_dependency_error(cycle)
                errors.append(error.format_error())
                logger.warning(
                    "Circular dependency detected in document chain: %s", " -> ".join(cycle)
                )
                return

            if doc_id in visited:
                return

            visited.add(doc_id)
            doc = lineage_data.get(doc_id)

            if doc and doc.derived_from:
                # Check derived_from relationship
                chain.add(doc_id)
                check_derivation_chain(doc.derived_from, chain)
                chain.remove(doc_id)

            # Also check derived_documents to catch any inconsistencies
            if doc and doc.derived_documents:
                for derived_id in doc.derived_documents:
                    chain.add(doc_id)
                    check_derivation_chain(derived_id, chain)
                    chain.remove(doc_id)

        # Check each document as a potential start of a cycle
        for doc_id in lineage_data:
            check_derivation_chain(doc_id, set())

            # Check for direct self-reference
            doc = lineage_data[doc_id]
            if doc.derived_from == doc_id:
                error = LineageValidationErrorFactory.create_circular_dependency_error([doc_id])
                errors.append(error.format_error())
                logger.warning("Document %s is derived from itself", doc_id)

        return errors
