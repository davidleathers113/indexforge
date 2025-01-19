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
import traceback

from src.core.interfaces.storage import LineageStorage
from src.core.models import DocumentLineage
from src.core.tracking.validation.interface import LineageValidationErrorFactory, ValidationStrategy


logger = logging.getLogger(__name__)


def validate_no_circular_reference(
    storage: LineageStorage,
    parent_id: str,
    child_id: str,
) -> bool:
    """Check if adding a parent-child relationship would create a circular reference.

    This function performs a depth-first search through the document derivation
    chain to detect if adding the proposed relationship would create a cycle.

    Args:
        storage: LineageStorage instance
        parent_id: ID of the proposed parent document
        child_id: ID of the proposed child document

    Returns:
        bool: True if a circular reference would be created, False otherwise

    Example:
        ```python
        if validate_no_circular_reference(storage, "doc1", "doc2"):
            raise ValueError("Adding this relationship would create a cycle")
        ```
    """
    logger.debug(
        "Starting circular reference validation - parent_id: %s, child_id: %s",
        parent_id,
        child_id,
    )

    if parent_id == child_id:
        logger.warning("Attempted direct self-reference detected: %s", parent_id)
        return True

    visited: set[str] = set()

    def check_ancestors(doc_id: str) -> bool:
        """Recursively check ancestors for cycles.

        Args:
            doc_id: Current document ID being checked

        Returns:
            bool: True if a cycle is found, False otherwise
        """
        logger.debug("Checking ancestors for document: %s", doc_id)

        if doc_id == child_id:
            logger.warning(
                "Circular reference detected: %s would become an ancestor of itself",
                child_id,
            )
            return True

        if doc_id in visited:
            logger.debug("Already visited document: %s, skipping", doc_id)
            return False

        visited.add(doc_id)
        try:
            doc = storage.get_lineage(doc_id)
            if doc is None:
                logger.warning("Document not found in storage: %s", doc_id)
                return False

            if doc.parents:
                logger.debug(
                    "Found parents for document %s: %s",
                    doc_id,
                    ", ".join(doc.parents),
                )
                for parent in doc.parents:
                    if check_ancestors(parent):
                        return True
            else:
                logger.debug("No parents found for document: %s", doc_id)

        except Exception as e:
            logger.error(
                "Error checking ancestors for document %s: %s\n%s",
                doc_id,
                str(e),
                traceback.format_exc(),
            )
            raise

        return False

    try:
        # Start checking from the parent's ancestors
        parent = storage.get_lineage(parent_id)
        if parent is None:
            logger.warning("Parent document not found: %s", parent_id)
            return False

        if parent.parents:
            logger.debug(
                "Starting ancestor check from parent %s with parents: %s",
                parent_id,
                ", ".join(parent.parents),
            )
            for ancestor_id in parent.parents:
                if check_ancestors(ancestor_id):
                    return True
        else:
            logger.debug("Parent document %s has no ancestors", parent_id)

    except Exception as e:
        logger.error(
            "Error during circular reference validation for parent %s and child %s: %s\n%s",
            parent_id,
            child_id,
            str(e),
            traceback.format_exc(),
        )
        raise

    logger.debug(
        "No circular reference found between parent %s and child %s",
        parent_id,
        child_id,
    )
    return False


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
        logger.debug("Starting circular dependency validation for %d documents", len(lineage_data))
        errors = []
        visited: set[str] = set()

        def check_derivation_chain(doc_id: str, chain: set[str]) -> None:
            """Recursively check derivation chain for cycles.

            Args:
                doc_id: Current document ID being checked
                chain: Set of document IDs in current chain
            """
            logger.debug(
                "Checking derivation chain for document %s. Current chain: %s",
                doc_id,
                " -> ".join(chain) if chain else "empty",
            )

            if doc_id in chain:
                # Found a cycle - create error with the cycle path
                cycle = list(chain)[list(chain).index(doc_id) :] + [doc_id]
                error = LineageValidationErrorFactory.create_circular_dependency_error(cycle)
                errors.append(error.format_error())
                logger.warning(
                    "Circular dependency detected in document chain: %s",
                    " -> ".join(cycle),
                )
                return

            if doc_id in visited:
                logger.debug("Already visited document: %s, skipping", doc_id)
                return

            visited.add(doc_id)
            try:
                doc = lineage_data.get(doc_id)
                if doc is None:
                    logger.warning("Document %s not found in lineage data", doc_id)
                    return

                if doc.derived_from:
                    logger.debug(
                        "Document %s is derived from %s, checking derivation",
                        doc_id,
                        doc.derived_from,
                    )
                    chain.add(doc_id)
                    check_derivation_chain(doc.derived_from, chain)
                    chain.remove(doc_id)

                if doc.derived_documents:
                    logger.debug(
                        "Document %s has derived documents: %s",
                        doc_id,
                        ", ".join(doc.derived_documents),
                    )
                    for derived_id in doc.derived_documents:
                        chain.add(doc_id)
                        check_derivation_chain(derived_id, chain)
                        chain.remove(doc_id)

            except Exception as e:
                logger.error(
                    "Error checking derivation chain for document %s: %s\n%s",
                    doc_id,
                    str(e),
                    traceback.format_exc(),
                )
                raise

        try:
            # Check each document as a potential start of a cycle
            for doc_id in lineage_data:
                logger.debug("Starting validation from document: %s", doc_id)
                check_derivation_chain(doc_id, set())

                # Check for direct self-reference
                doc = lineage_data[doc_id]
                if doc.derived_from == doc_id:
                    error = LineageValidationErrorFactory.create_circular_dependency_error([doc_id])
                    errors.append(error.format_error())
                    logger.warning("Document %s is derived from itself", doc_id)

        except Exception as e:
            logger.error(
                "Error during circular dependency validation: %s\n%s",
                str(e),
                traceback.format_exc(),
            )
            raise

        if errors:
            logger.warning(
                "Found %d circular dependencies in document lineage",
                len(errors),
            )
        else:
            logger.debug("No circular dependencies found in document lineage")

        return errors


__all__ = [
    "CircularDependencyValidator",
    "validate_no_circular_reference",
]
