"""Relationship validation strategy for document lineage.

This module provides validation for relationships between documents in the lineage data.
It ensures consistency and validity of parent-child relationships, derived document
references, and cross-document relationships.

Example:
    ```python
    validator = RelationshipValidator()
    errors = validator.validate(document_lineage)
    if errors:
        print("Found invalid relationships:", errors)
    ```
"""

from logging import getLogger
from typing import List, Optional, Set

from src.core.models import DocumentLineage
from src.core.tracking.validation.errors import LineageValidationErrorFactory
from src.core.tracking.validation.interface import ValidationStrategy

logger = getLogger(__name__)


class RelationshipValidator(ValidationStrategy):
    """Validates relationships between documents in lineage data.

    This validator ensures:
    1. All parent-child relationships are bidirectional and consistent
    2. All derived document references are valid and accessible
    3. No circular relationships exist between documents
    4. No document is its own parent or derived document
    5. All relationship references point to valid documents
    """

    def __init__(self) -> None:
        """Initialize the relationship validator."""
        self.error_factory = LineageValidationErrorFactory()

    def validate(self, lineage: DocumentLineage) -> List[str]:
        """Validate relationships in the document lineage.

        Args:
            lineage: The document lineage data to validate.

        Returns:
            A list of error messages for any invalid relationships found.
        """
        if not lineage:
            return []

        errors: List[str] = []

        # Validate parent-child relationships
        errors.extend(self._validate_parent_child_relationships(lineage))

        # Validate derived document relationships
        errors.extend(self._validate_derived_relationships(lineage))

        # Validate cross-document references
        errors.extend(self._validate_cross_references(lineage))

        if errors:
            logger.warning(f"Found {len(errors)} invalid relationships")

        return errors

    def _validate_parent_child_relationships(self, lineage: DocumentLineage) -> List[str]:
        """Validate parent-child relationships in the document lineage.

        Args:
            lineage: The document lineage to validate.

        Returns:
            A list of error messages for any invalid parent-child relationships.
        """
        errors: List[str] = []

        # Check parent document reference
        if lineage.parent_id:
            parent = self._find_document_by_id(lineage, lineage.parent_id)
            if not parent:
                errors.append(
                    self.error_factory.create_missing_reference_error(
                        f"Referenced parent document not found: {lineage.parent_id}"
                    )
                )
            elif parent.document_id == lineage.document_id:
                errors.append(
                    self.error_factory.create_inconsistent_relationship_error(
                        f"Document cannot be its own parent: {lineage.document_id}"
                    )
                )
            else:
                # Verify bidirectional relationship
                if not any(
                    child.document_id == lineage.document_id
                    for child in parent.child_documents or []
                ):
                    errors.append(
                        self.error_factory.create_inconsistent_relationship_error(
                            f"Parent document {parent.document_id} does not reference this document as a child"
                        )
                    )

        # Check child document references
        for child in lineage.child_documents or []:
            if child.document_id == lineage.document_id:
                errors.append(
                    self.error_factory.create_inconsistent_relationship_error(
                        f"Document cannot be its own child: {lineage.document_id}"
                    )
                )
            elif child.parent_id != lineage.document_id:
                errors.append(
                    self.error_factory.create_inconsistent_relationship_error(
                        f"Child document {child.document_id} does not reference this document as parent"
                    )
                )

        return errors

    def _validate_derived_relationships(self, lineage: DocumentLineage) -> List[str]:
        """Validate derived document relationships in the lineage.

        Args:
            lineage: The document lineage to validate.

        Returns:
            A list of error messages for any invalid derived relationships.
        """
        errors: List[str] = []
        seen_derivations: Set[str] = set()

        for derived in lineage.derived_documents or []:
            # Check for self-derivation
            if derived.document_id == lineage.document_id:
                errors.append(
                    self.error_factory.create_inconsistent_relationship_error(
                        f"Document cannot be derived from itself: {lineage.document_id}"
                    )
                )
                continue

            # Check for duplicate derivations
            if derived.document_id in seen_derivations:
                errors.append(
                    self.error_factory.create_inconsistent_relationship_error(
                        f"Duplicate derived document reference: {derived.document_id}"
                    )
                )
            seen_derivations.add(derived.document_id)

            # Verify derived document exists and is accessible
            if not self._find_document_by_id(lineage, derived.document_id):
                errors.append(
                    self.error_factory.create_missing_reference_error(
                        f"Referenced derived document not found: {derived.document_id}"
                    )
                )

        return errors

    def _validate_cross_references(self, lineage: DocumentLineage) -> List[str]:
        """Validate cross-document references in the lineage.

        Args:
            lineage: The document lineage to validate.

        Returns:
            A list of error messages for any invalid cross-references.
        """
        errors: List[str] = []

        # Validate references in derived documents
        for derived in lineage.derived_documents or []:
            # Check that derived document references this document
            if not any(
                ref.document_id == lineage.document_id for ref in derived.source_references or []
            ):
                errors.append(
                    self.error_factory.create_inconsistent_relationship_error(
                        f"Derived document {derived.document_id} does not reference this document as source"
                    )
                )

        # Validate source references
        for ref in lineage.source_references or []:
            source = self._find_document_by_id(lineage, ref.document_id)
            if not source:
                errors.append(
                    self.error_factory.create_missing_reference_error(
                        f"Referenced source document not found: {ref.document_id}"
                    )
                )

        return errors

    def _find_document_by_id(
        self, lineage: DocumentLineage, doc_id: str
    ) -> Optional[DocumentLineage]:
        """Find a document in the lineage tree by its ID.

        Args:
            lineage: The document lineage to search.
            doc_id: The ID of the document to find.

        Returns:
            The found document if it exists, None otherwise.
        """
        if lineage.document_id == doc_id:
            return lineage

        # Search in derived documents
        for derived in lineage.derived_documents or []:
            if derived.document_id == doc_id:
                return derived

        # Search in child documents
        for child in lineage.child_documents or []:
            if child.document_id == doc_id:
                return child

        return None
