"""
Document lineage tracking implementation.

This module handles the tracking of document relationships and lineage,
including parent-child relationships and derivation history.
"""

import logging
from datetime import UTC, datetime
from typing import Any, Dict, Optional, Set

from src.core.tracking.models import DocumentLineage
from src.core.tracking.validation.strategies import validate_no_circular_reference

logger = logging.getLogger(__name__)


class DocumentLineageTracker:
    """Manages document lineage relationships and history."""

    def __init__(self, storage: Any):  # TODO: Add proper LineageStorage type once migrated
        """Initialize the document lineage tracker.

        Args:
            storage: Storage backend for lineage data
        """
        self.storage = storage
        logger.debug("Initialized DocumentLineageTracker with storage: %s", storage)

    def get_ancestors(self, doc_id: str, max_depth: Optional[int] = None) -> Set[str]:
        """Get all ancestor documents of the given document.

        Args:
            doc_id: ID of the document to get ancestors for
            max_depth: Optional maximum depth to traverse up the ancestry tree

        Returns:
            Set of ancestor document IDs

        Raises:
            ValueError: If document not found
        """
        logger.debug("Getting ancestors for document %s (max_depth=%s)", doc_id, max_depth)
        ancestors: Set[str] = set()
        to_process = [(doc_id, 0)]
        processed = set()

        while to_process:
            current_id, depth = to_process.pop(0)
            if current_id in processed:
                continue
            processed.add(current_id)

            if max_depth is not None and depth > max_depth:
                continue

            doc = self.storage.get_lineage(current_id)
            if not doc and current_id == doc_id:
                logger.error("Document not found: %s", doc_id)
                raise ValueError(f"Document not found: {doc_id}")

            if doc and doc.parents:
                for parent_id in doc.parents:
                    if parent_id not in processed:
                        ancestors.add(parent_id)
                        to_process.append((parent_id, depth + 1))

        logger.debug("Found %d ancestors for document %s", len(ancestors), doc_id)
        return ancestors

    def get_descendants(self, doc_id: str, max_depth: Optional[int] = None) -> Set[str]:
        """Get all descendant documents of the given document.

        Args:
            doc_id: ID of the document to get descendants for
            max_depth: Optional maximum depth to traverse down the descendant tree

        Returns:
            Set of descendant document IDs

        Raises:
            ValueError: If document not found
        """
        logger.debug("Getting descendants for document %s (max_depth=%s)", doc_id, max_depth)
        descendants: Set[str] = set()
        to_process = [(doc_id, 0)]
        processed = set()

        while to_process:
            current_id, depth = to_process.pop(0)
            if current_id in processed:
                continue
            processed.add(current_id)

            if max_depth is not None and depth > max_depth:
                continue

            doc = self.storage.get_lineage(current_id)
            if not doc and current_id == doc_id:
                logger.error("Document not found: %s", doc_id)
                raise ValueError(f"Document not found: {doc_id}")

            if doc and doc.children:
                for child_id in doc.children:
                    if child_id not in processed:
                        descendants.add(child_id)
                        to_process.append((child_id, depth + 1))

        logger.debug("Found %d descendants for document %s", len(descendants), doc_id)
        return descendants

    def add_parent(self, doc_id: str, parent_id: str) -> None:
        """Add a parent relationship to a document.

        Args:
            doc_id: ID of the child document
            parent_id: ID of the parent document to add

        Raises:
            ValueError: If either document not found or would create circular reference
        """
        logger.info("Adding parent %s to document %s", parent_id, doc_id)

        # Verify both documents exist
        doc = self.storage.get_lineage(doc_id)
        parent = self.storage.get_lineage(parent_id)

        if not doc:
            logger.error("Child document not found: %s", doc_id)
            raise ValueError(f"Child document not found: {doc_id}")
        if not parent:
            logger.error("Parent document not found: %s", parent_id)
            raise ValueError(f"Parent document not found: {parent_id}")

        # Check for circular references
        if validate_no_circular_reference(self.storage, parent_id, doc_id):
            logger.error(
                "Circular reference detected - Parent: %s, Child: %s would create a cycle",
                parent_id,
                doc_id,
            )
            raise ValueError(
                f"Circular reference detected: adding {doc_id} as child of {parent_id} would create a cycle"
            )

        # Update relationships
        current_time = datetime.now(UTC)

        if parent_id not in doc.parents:
            logger.debug("Adding %s to document %s's parents list", parent_id, doc_id)
            doc.parents.append(parent_id)
            if not doc.derived_from:
                doc.derived_from = parent_id
            doc.last_modified = current_time
            self.storage.save_lineage(doc)

        if doc_id not in parent.children:
            logger.debug("Adding %s to parent %s's children list", doc_id, parent_id)
            parent.children.append(doc_id)
            parent.derived_documents.append(doc_id)
            parent.last_modified = current_time
            self.storage.save_lineage(parent)

        logger.info("Successfully added parent relationship")

    def remove_parent(self, doc_id: str, parent_id: str) -> None:
        """Remove a parent relationship from a document.

        Args:
            doc_id: ID of the child document
            parent_id: ID of the parent document to remove

        Raises:
            ValueError: If either document not found
        """
        logger.info("Removing parent %s from document %s", parent_id, doc_id)

        # Verify both documents exist
        doc = self.storage.get_lineage(doc_id)
        parent = self.storage.get_lineage(parent_id)

        if not doc:
            logger.error("Child document not found: %s", doc_id)
            raise ValueError(f"Child document not found: {doc_id}")
        if not parent:
            logger.error("Parent document not found: %s", parent_id)
            raise ValueError(f"Parent document not found: {parent_id}")

        # Update relationships
        current_time = datetime.now(UTC)
        modified = False

        if parent_id in doc.parents:
            logger.debug("Removing %s from document %s's parents list", parent_id, doc_id)
            doc.parents.remove(parent_id)
            if doc.derived_from == parent_id:
                doc.derived_from = doc.parents[0] if doc.parents else None
            doc.last_modified = current_time
            self.storage.save_lineage(doc)
            modified = True

        if doc_id in parent.children:
            logger.debug("Removing %s from parent %s's children list", doc_id, parent_id)
            parent.children.remove(doc_id)
            if doc_id in parent.derived_documents:
                parent.derived_documents.remove(doc_id)
            parent.last_modified = current_time
            self.storage.save_lineage(parent)
            modified = True

        if modified:
            logger.info("Successfully removed parent relationship")
        else:
            logger.warning("No relationship found between documents")

    def get_lineage_info(self, doc_id: str) -> Dict[str, Any]:
        """Get comprehensive lineage information for a document.

        Args:
            doc_id: ID of the document to get lineage info for

        Returns:
            Dictionary containing lineage information including:
            - ancestors: Set of ancestor document IDs
            - descendants: Set of descendant document IDs
            - direct_parents: List of immediate parent IDs
            - direct_children: List of immediate child IDs
            - metadata: Document metadata
            - created_at: Creation timestamp
            - last_modified: Last modification timestamp

        Raises:
            ValueError: If document not found
        """
        logger.debug("Getting lineage info for document %s", doc_id)
        doc = self.storage.get_lineage(doc_id)
        if not doc:
            logger.error("Document not found: %s", doc_id)
            raise ValueError(f"Document not found: {doc_id}")

        ancestors = self.get_ancestors(doc_id)
        descendants = self.get_descendants(doc_id)

        info = {
            "ancestors": ancestors,
            "descendants": descendants,
            "direct_parents": doc.parents,
            "direct_children": doc.children,
            "derived_from": doc.derived_from,
            "derived_documents": doc.derived_documents,
            "metadata": doc.metadata,
            "created_at": doc.created_at,
            "last_modified": doc.last_modified,
            "origin_id": doc.origin_id,
            "origin_source": doc.origin_source,
            "origin_type": doc.origin_type,
        }

        logger.debug("Retrieved lineage info for document %s: %s", doc_id, info)
        return info
