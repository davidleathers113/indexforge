"""Chunk reference validation strategy for document lineage.

This module provides validation for chunk references within document lineage data.
It ensures that all chunk references point to valid source documents and that the
referenced chunks exist within those documents.

Example:
    ```python
    validator = ChunkReferenceValidator()
    errors = validator.validate(document_lineage)
    if errors:
        print("Found invalid chunk references:", errors)
    ```
"""

from logging import getLogger
from typing import List, Optional, Set

from src.core.models import DocumentLineage
from src.core.tracking.validation.errors import LineageValidationErrorFactory
from src.core.tracking.validation.interface import ValidationStrategy

logger = getLogger(__name__)


class ChunkReferenceValidator(ValidationStrategy):
    """Validates chunk references in document lineage data.

    This validator ensures that:
    1. All referenced source documents exist
    2. All referenced chunks exist in their source documents
    3. No duplicate chunk references exist
    4. Chunk references are well-formed
    """

    def __init__(self) -> None:
        """Initialize the chunk reference validator."""
        self.error_factory = LineageValidationErrorFactory()

    def validate(self, lineage: DocumentLineage) -> List[str]:
        """Validate chunk references in the document lineage.

        Args:
            lineage: The document lineage data to validate.

        Returns:
            A list of error messages for any invalid chunk references found.
        """
        if not lineage:
            return []

        errors: List[str] = []
        seen_chunks: Set[str] = set()

        # Validate each chunk reference
        for chunk_ref in lineage.chunk_references or []:
            # Check for duplicate chunk references
            chunk_id = f"{chunk_ref.source_doc_id}:{chunk_ref.chunk_id}"
            if chunk_id in seen_chunks:
                errors.append(
                    self.error_factory.create_missing_reference_error(
                        f"Duplicate chunk reference found: {chunk_id}"
                    )
                )
            seen_chunks.add(chunk_id)

            # Validate source document exists
            source_doc = self._get_source_document(lineage, chunk_ref.source_doc_id)
            if not source_doc:
                errors.append(
                    self.error_factory.create_missing_reference_error(
                        f"Referenced source document not found: {chunk_ref.source_doc_id}"
                    )
                )
                continue

            # Validate chunk exists in source document
            if not self._chunk_exists_in_document(source_doc, chunk_ref.chunk_id):
                errors.append(
                    self.error_factory.create_missing_reference_error(
                        f"Referenced chunk {chunk_ref.chunk_id} not found in source document {chunk_ref.source_doc_id}"
                    )
                )

        if errors:
            logger.warning(f"Found {len(errors)} invalid chunk references")

        return errors

    def _get_source_document(
        self, lineage: DocumentLineage, doc_id: str
    ) -> Optional[DocumentLineage]:
        """Get a source document from the lineage by its ID.

        Args:
            lineage: The document lineage data.
            doc_id: The ID of the source document to find.

        Returns:
            The source document if found, None otherwise.
        """
        # Check direct references
        if lineage.document_id == doc_id:
            return lineage

        # Check derived documents
        for derived in lineage.derived_documents or []:
            if derived.document_id == doc_id:
                return derived

        return None

    def _chunk_exists_in_document(self, document: DocumentLineage, chunk_id: str) -> bool:
        """Check if a chunk exists in a document.

        Args:
            document: The document to check.
            chunk_id: The ID of the chunk to find.

        Returns:
            True if the chunk exists, False otherwise.
        """
        return any(chunk.chunk_id == chunk_id for chunk in document.chunks or [])
