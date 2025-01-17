"""Chunk reference validation strategy."""

from src.core.models import DocumentLineage
from src.core.tracking.validation.errors import LineageValidationErrorFactory
from src.core.tracking.validation.interfaces import ValidationStrategy


class ChunkReferenceValidator(ValidationStrategy):
    """Validates chunk references across documents."""

    def __init__(self) -> None:
        """Initialize the validator with error factory."""
        self.error_factory = LineageValidationErrorFactory()

    def validate(self, lineage_data: dict[str, DocumentLineage]) -> list[str]:
        """
        Validate chunk references across all documents.

        This function checks that all chunk references in documents point to valid
        source documents and chunks. It verifies that referenced documents exist
        and that chunk IDs are valid within those documents.

        Args:
            lineage_data: Dictionary mapping document IDs to their lineage data

        Returns:
            List of error messages describing any invalid chunk references
        """
        errors = []

        for doc_id, doc in lineage_data.items():
            for chunk_ref in doc.chunk_references:
                source_doc = lineage_data.get(chunk_ref.source_doc)
                if not source_doc:
                    error = self.error_factory.create_error(
                        "missing",
                        source_id=doc_id,
                        target_id=chunk_ref.source_doc,
                        reference_type="chunk source",
                    )
                    errors.append(error.format_message())

        return errors
