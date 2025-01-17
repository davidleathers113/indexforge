"""Document lineage management for IndexForge.

This module provides the lineage manager responsible for storing and
retrieving document lineage information, including version history
and relationship tracking.
"""

import asyncio
from uuid import UUID

from src.core.lineage.base import ChangeType, DocumentLineage, SourceInfo
from src.core.schema.base import ValidationError


class LineageError(Exception):
    """Base class for lineage-related errors."""

    pass


class CircularReferenceError(LineageError):
    """Raised when a circular reference is detected."""

    pass


class LineageManager:
    """Manager for handling document lineage information."""

    def __init__(self):
        """Initialize lineage manager."""
        self._lineage: dict[UUID, DocumentLineage] = {}
        self._lock = asyncio.Lock()

    async def get_lineage(self, document_id: UUID) -> DocumentLineage | None:
        """Get lineage information for a document.

        Args:
            document_id: Document ID to get lineage for

        Returns:
            Document lineage if found, None otherwise
        """
        async with self._lock:
            return self._lineage.get(document_id)

    async def create_lineage(
        self,
        document_id: UUID,
        source_info: SourceInfo | None = None,
        parent_id: UUID | None = None,
    ) -> DocumentLineage:
        """Create new lineage for a document.

        Args:
            document_id: Document ID to create lineage for
            source_info: Optional source information
            parent_id: Optional ID of parent document

        Returns:
            Created document lineage

        Raises:
            LineageError: If lineage already exists
            ValidationError: If parent document doesn't exist
        """
        async with self._lock:
            if document_id in self._lineage:
                raise LineageError(f"Lineage already exists for document {document_id}")

            if parent_id and parent_id not in self._lineage:
                raise ValidationError(f"Parent document {parent_id} not found")

            lineage = DocumentLineage(
                document_id=document_id,
                source_info=source_info,
                parent_id=parent_id,
            )

            # Add initial change record
            lineage.add_change(
                change_type=ChangeType.CREATED,
                source_info=source_info,
                parent_id=parent_id,
            )

            # Update parent's children if needed
            if parent_id:
                parent = self._lineage[parent_id]
                parent.children_ids.add(document_id)
                parent.add_change(
                    change_type=ChangeType.PROCESSED,
                    metadata={"child_document": str(document_id)},
                )

            self._lineage[document_id] = lineage
            return lineage

    async def update_lineage(
        self,
        document_id: UUID,
        change_type: ChangeType,
        source_info: SourceInfo | None = None,
        metadata: dict[str, str] | None = None,
        related_ids: set[UUID] | None = None,
    ) -> DocumentLineage:
        """Update lineage for a document.

        Args:
            document_id: Document ID to update lineage for
            change_type: Type of change that occurred
            source_info: Optional source information
            metadata: Optional metadata about the change
            related_ids: Optional set of related document IDs

        Returns:
            Updated document lineage

        Raises:
            LineageError: If lineage doesn't exist or circular reference detected
            ValidationError: If related documents don't exist
        """
        async with self._lock:
            lineage = self._lineage.get(document_id)
            if not lineage:
                raise LineageError(f"No lineage found for document {document_id}")

            # Validate related documents exist
            if related_ids:
                missing = related_ids - set(self._lineage.keys())
                if missing:
                    raise ValidationError(f"Related documents not found: {missing}")

                # Check for circular references
                if change_type == ChangeType.REFERENCED:
                    await self._check_circular_references(document_id, related_ids)

            # Update lineage
            lineage.add_change(
                change_type=change_type,
                source_info=source_info,
                metadata=metadata,
                related_ids=related_ids,
            )

            # Update related documents if needed
            if related_ids:
                if change_type == ChangeType.REFERENCED:
                    for ref_id in related_ids:
                        ref = self._lineage[ref_id]
                        ref.referenced_by_ids.add(document_id)
                        ref.add_change(
                            change_type=ChangeType.REFERENCED,
                            metadata={"referenced_by": str(document_id)},
                        )
                elif change_type == ChangeType.DEREFERENCED:
                    for ref_id in related_ids:
                        ref = self._lineage[ref_id]
                        ref.referenced_by_ids.discard(document_id)
                        ref.add_change(
                            change_type=ChangeType.DEREFERENCED,
                            metadata={"dereferenced_by": str(document_id)},
                        )

            return lineage

    async def delete_lineage(self, document_id: UUID) -> None:
        """Delete lineage for a document.

        This will also update any related documents to remove references
        to the deleted document.

        Args:
            document_id: Document ID to delete lineage for

        Raises:
            LineageError: If lineage doesn't exist
        """
        async with self._lock:
            lineage = self._lineage.get(document_id)
            if not lineage:
                raise LineageError(f"No lineage found for document {document_id}")

            # Update parent document
            if lineage.parent_id:
                parent = self._lineage[lineage.parent_id]
                parent.children_ids.discard(document_id)
                parent.add_change(
                    change_type=ChangeType.PROCESSED,
                    metadata={"removed_child": str(document_id)},
                )

            # Update referenced documents
            for ref_id in lineage.reference_ids:
                ref = self._lineage[ref_id]
                ref.referenced_by_ids.discard(document_id)
                ref.add_change(
                    change_type=ChangeType.DEREFERENCED,
                    metadata={"dereferenced_by": str(document_id)},
                )

            # Update documents referencing this one
            for ref_id in lineage.referenced_by_ids:
                ref = self._lineage[ref_id]
                ref.reference_ids.discard(document_id)
                ref.add_change(
                    change_type=ChangeType.DEREFERENCED,
                    metadata={"removed_reference": str(document_id)},
                )

            # Add final change record and remove
            lineage.add_change(change_type=ChangeType.DELETED)
            del self._lineage[document_id]

    async def get_document_history(
        self,
        document_id: UUID,
        since_version: int | None = None,
    ) -> list[dict[str, str]]:
        """Get change history for a document.

        Args:
            document_id: Document ID to get history for
            since_version: Optional version to get changes since

        Returns:
            List of change records as dictionaries

        Raises:
            LineageError: If lineage doesn't exist
        """
        async with self._lock:
            lineage = self._lineage.get(document_id)
            if not lineage:
                raise LineageError(f"No lineage found for document {document_id}")

            if since_version is not None:
                changes = lineage.get_changes_since(since_version)
            else:
                changes = lineage.history

            return [change.dict() for change in changes]

    async def _check_circular_references(
        self,
        document_id: UUID,
        reference_ids: set[UUID],
        visited: set[UUID] | None = None,
    ) -> None:
        """Check for circular references in the document graph.

        Args:
            document_id: Current document ID
            reference_ids: Set of document IDs being referenced
            visited: Set of already visited document IDs

        Raises:
            CircularReferenceError: If circular reference is detected
        """
        visited = visited or {document_id}

        for ref_id in reference_ids:
            if ref_id in visited:
                raise CircularReferenceError(
                    f"Circular reference detected: {document_id} -> {ref_id}"
                )

            ref = self._lineage.get(ref_id)
            if ref and ref.reference_ids:
                next_visited = visited | {ref_id}
                await self._check_circular_references(ref_id, ref.reference_ids, next_visited)
