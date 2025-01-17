"""Relationship validation strategy."""

from src.core.models import DocumentLineage
from src.core.tracking.validation.errors import LineageValidationErrorFactory
from src.core.tracking.validation.interfaces import ValidationStrategy


class RelationshipValidator(ValidationStrategy):
    """Validates relationships between documents."""

    def __init__(self) -> None:
        """Initialize the validator with error factory."""
        self.error_factory = LineageValidationErrorFactory()

    def validate(self, lineage_data: dict[str, DocumentLineage]) -> list[str]:
        """
        Validate relationships between documents in the lineage data.

        This function performs comprehensive validation of document relationships,
        including:
        - Derived document references
        - Parent-child relationships
        - Cross-document references
        - Relationship consistency

        Args:
            lineage_data: Dictionary mapping document IDs to their lineage data

        Returns:
            List of error messages describing any invalid relationships
        """
        errors = []

        for doc_id, doc in lineage_data.items():
            # Validate derived_from references
            if doc.derived_from:
                if doc.derived_from not in lineage_data:
                    error = self.error_factory.create_error(
                        "missing",
                        source_id=doc_id,
                        target_id=doc.derived_from,
                        reference_type="parent",
                    )
                    errors.append(error.format_message())
                elif doc.derived_from == doc_id:
                    error = self.error_factory.create_error(
                        "inconsistent",
                        source_id=doc_id,
                        target_id=doc_id,
                        relationship_type="derivation",
                        details="cannot be derived from itself",
                    )
                    errors.append(error.format_message())

            # Validate parent-child relationships
            for child_id in doc.children:
                if child_id not in lineage_data:
                    error = self.error_factory.create_error(
                        "missing", source_id=doc_id, target_id=child_id, reference_type="child"
                    )
                    errors.append(error.format_message())
                else:
                    child_doc = lineage_data[child_id]
                    if doc_id not in child_doc.parents:
                        error = self.error_factory.create_error(
                            "inconsistent",
                            source_id=doc_id,
                            target_id=child_id,
                            relationship_type="parent-child",
                            details="lists as child, but child does not list as parent",
                        )
                        errors.append(error.format_message())

            # Validate parent references
            for parent_id in doc.parents:
                if parent_id not in lineage_data:
                    error = self.error_factory.create_error(
                        "missing", source_id=doc_id, target_id=parent_id, reference_type="parent"
                    )
                    errors.append(error.format_message())
                else:
                    parent_doc = lineage_data[parent_id]
                    if doc_id not in parent_doc.children:
                        error = self.error_factory.create_error(
                            "inconsistent",
                            source_id=doc_id,
                            target_id=parent_id,
                            relationship_type="parent-child",
                            details="lists as parent, but parent does not list as child",
                        )
                        errors.append(error.format_message())

            # Validate derived documents
            for derived_id in doc.derived_documents:
                if derived_id not in lineage_data:
                    error = self.error_factory.create_error(
                        "missing", source_id=doc_id, target_id=derived_id, reference_type="derived"
                    )
                    errors.append(error.format_message())
                else:
                    derived_doc = lineage_data[derived_id]
                    if derived_doc.derived_from != doc_id:
                        error = self.error_factory.create_error(
                            "inconsistent",
                            source_id=doc_id,
                            target_id=derived_id,
                            relationship_type="derivation",
                            details=f"lists as derived, but derived document lists {derived_doc.derived_from} as parent",
                        )
                        errors.append(error.format_message())

        return errors
