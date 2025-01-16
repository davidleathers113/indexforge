"""
Manages document lineage operations and relationships.

This module provides functionality for managing relationships between documents,
including derivation chains and parent-child relationships.
"""

from datetime import UTC, datetime
import logging

from .enums import TransformationType
from .models import DocumentLineage
from .transformation_manager import record_transformation


logger = logging.getLogger(__name__)


def add_derivation(
    storage,
    parent_id: str,
    derived_id: str,
    transform_type: TransformationType | str | None = None,
    description: str = "",
    parameters: dict | None = None,
    metadata: dict | None = None,
) -> None:
    """Link a derived document to its parent.

    Args:
        storage: LineageStorage instance
        parent_id: ID of the parent document
        derived_id: ID of the derived document
        transform_type: Type of transformation applied
        description: Description of the derivation
        parameters: Parameters used in the transformation
        metadata: Additional metadata about the derivation

    Raises:
        ValueError: If parent or derived document not found, or if circular reference detected
    """
    logger.info(
        "Adding derivation relationship - Parent: %s, Derived: %s",
        parent_id,
        derived_id,
    )
    logger.debug("Transform type: %s, Description: %s", transform_type, description)
    logger.debug("Parameters: %s", parameters)
    logger.debug("Metadata: %s", metadata)

    # Validate input parameters
    if not parent_id or not derived_id:
        logger.error("Invalid document IDs - Parent: %s, Derived: %s", parent_id, derived_id)
        raise ValueError("Parent and derived document IDs must be provided")

    # Check for self-referential derivation
    if parent_id == derived_id:
        logger.error("Attempted to create self-referential derivation for document %s", parent_id)
        raise ValueError("Document cannot be derived from itself")

    try:
        # Get parent lineage
        parent_lineage = storage.get_lineage(parent_id)
        if not parent_lineage:
            logger.error("Parent document %s not found in lineage tracking", parent_id)
            raise ValueError(f"Parent document {parent_id} not found")
        logger.debug("Parent lineage found: %s", parent_lineage)

        # Get derived lineage
        derived_lineage = storage.get_lineage(derived_id)
        if not derived_lineage:
            logger.error("Derived document %s not found in lineage tracking", derived_id)
            raise ValueError(f"Derived document {derived_id} not found")
        logger.debug("Derived lineage found: %s", derived_lineage)

        # Check for circular references
        if _would_create_circular_reference(storage, parent_id, derived_id):
            logger.error(
                "Circular reference detected: %s -> %s would create a cycle",
                parent_id,
                derived_id,
            )
            raise ValueError(
                f"Circular reference detected: adding {derived_id} as parent of {parent_id} would create a cycle"
            )

        # Update parent document
        if derived_id not in parent_lineage.derived_documents:
            logger.debug("Adding %s to parent's derived documents", derived_id)
            parent_lineage.derived_documents.append(derived_id)
            parent_lineage.children.append(derived_id)
            parent_lineage.last_modified = datetime.now(UTC)
            storage.save_lineage(parent_lineage)
            logger.debug(
                "Updated parent lineage - Derived docs: %s, Children: %s",
                parent_lineage.derived_documents,
                parent_lineage.children,
            )

        # Update derived document
        if parent_id not in derived_lineage.parents:
            logger.debug("Adding %s to derived document's parents", parent_id)
            derived_lineage.parents.append(parent_id)
            derived_lineage.derived_from = parent_id  # Set the direct parent
            derived_lineage.last_modified = datetime.now(UTC)
            storage.save_lineage(derived_lineage)
            logger.debug("Updated derived lineage - Parents: %s", derived_lineage.parents)

        # Record transformation if specified
        if transform_type:
            logger.debug("Recording transformation of type %s", transform_type)
            try:
                record_transformation(
                    storage=storage,
                    doc_id=derived_id,  # Record transformation on derived document
                    transform_type=transform_type,
                    description=description,
                    parameters=parameters,
                    metadata=metadata,
                )
            except Exception as e:
                logger.error("Failed to record transformation: %s", str(e))
                raise

        logger.info("Successfully added derivation relationship %s -> %s", parent_id, derived_id)

    except Exception as e:
        logger.error("Failed to add derivation relationship: %s", str(e))
        raise


def get_derivation_chain(
    storage,
    doc_id: str,
    max_depth: int | None = None,
) -> list[DocumentLineage]:
    """Get the chain of document derivations leading to the given document.

    Args:
        storage: LineageStorage instance
        doc_id: ID of the document to get derivation chain for
        max_depth: Maximum depth to traverse in the chain

    Returns:
        List of DocumentLineage objects representing the derivation chain from newest to oldest

    Raises:
        ValueError: If document not found or max_depth is invalid
    """
    logger.info("Getting derivation chain for document %s (max depth: %s)", doc_id, max_depth)

    # First, let's log all document relationships for debugging
    all_lineages = storage.get_all_lineage()
    logger.debug("All document relationships:")
    for doc_id_iter, lineage in all_lineages.items():
        logger.debug(
            "Document %s - Parents: %s, Children: %s, Derived: %s",
            doc_id_iter,
            lineage.parents,
            lineage.children,
            lineage.derived_documents,
        )

    # Validate input parameters
    if not doc_id:
        logger.error("Invalid document ID provided")
        raise ValueError("Document ID must be provided")

    if max_depth is not None and max_depth < 0:
        logger.error("Invalid max_depth value: %d", max_depth)
        raise ValueError("max_depth must be a non-negative integer")

    try:
        # Initialize chain tracking
        chain = []
        current_id = doc_id
        visited = set()
        depth = 0

        logger.debug("Starting chain traversal from document %s", current_id)

        # First traverse to the root
        root_id = current_id
        while current_id and (max_depth is None or depth < max_depth):
            lineage = storage.get_lineage(current_id)
            if not lineage:
                logger.error("Document %s not found in lineage tracking", current_id)
                raise ValueError(f"Document {current_id} not found in lineage tracking")

            logger.debug(
                "Traversing to root - Current: %s, Parents: %s, Children: %s, Derived: %s",
                current_id,
                lineage.parents,
                lineage.children,
                lineage.derived_documents,
            )

            if current_id in visited:
                logger.warning(
                    "Circular reference detected at document %s, stopping traversal",
                    current_id,
                )
                break

            visited.add(current_id)
            if not lineage.parents:
                logger.debug("Found root document %s (no parents)", current_id)
                root_id = current_id
                break

            current_id = lineage.parents[0]
            logger.debug("Moving to parent: %s", current_id)
            depth += 1

        logger.debug("Root traversal complete - Root: %s, Depth: %d", root_id, depth)

        # Now build chain from root to target
        chain = []
        current_id = root_id
        visited = set()
        depth = 0

        # Log the target document's lineage for debugging
        target_lineage = storage.get_lineage(doc_id)
        if target_lineage:
            logger.debug(
                "Target document state - ID: %s, Parents: %s, Children: %s, Derived: %s",
                doc_id,
                target_lineage.parents,
                target_lineage.children,
                target_lineage.derived_documents,
            )

        # Find path from root to target
        def find_path_to_target(
            start_id: str, target_id: str, path: list[str] = None
        ) -> list[str] | None:
            """Find a path from start_id to target_id through derived documents."""
            if path is None:
                path = []

            if start_id in path:
                logger.debug("Circular path detected at %s", start_id)
                return None

            current = storage.get_lineage(start_id)
            if not current:
                logger.debug("Document %s not found", start_id)
                return None

            new_path = path + [start_id]
            logger.debug("Checking path: %s", new_path)

            if start_id == target_id:
                logger.debug("Found path to target: %s", new_path)
                return new_path

            if target_id in current.derived_documents:
                logger.debug("Found direct path: %s -> %s", new_path, target_id)
                return new_path + [target_id]

            for derived_id in current.derived_documents:
                logger.debug("Checking derived document %s from %s", derived_id, start_id)
                result = find_path_to_target(derived_id, target_id, new_path)
                if result:
                    logger.debug("Found path through %s: %s", derived_id, result)
                    return result

            logger.debug("No path found from %s to %s", start_id, target_id)
            return None

        # Find the path from root to target
        path = find_path_to_target(root_id, doc_id)
        if path:
            logger.debug("Found complete path: %s", path)
            # Build chain from path
            chain = [storage.get_lineage(doc_id) for doc_id in path]
            logger.debug(
                "Built chain with %d documents: %s", len(chain), [doc.doc_id for doc in chain]
            )
        else:
            logger.error(
                "No valid path found from root %s to target %s",
                root_id,
                doc_id,
            )

        logger.info(
            "Chain building complete - Length: %d, Chain: %s",
            len(chain),
            [doc.doc_id for doc in chain],
        )

        # Return chain in newest to oldest order
        return list(reversed(chain))

    except Exception as e:
        logger.error("Failed to get derivation chain: %s", str(e))
        raise


def _would_create_circular_reference(storage, parent_id: str, derived_id: str) -> bool:
    """Check if adding a derivation would create a circular reference.

    Args:
        storage: LineageStorage instance
        parent_id: ID of the parent document
        derived_id: ID of the derived document

    Returns:
        True if adding the derivation would create a circular reference
    """
    logger.debug(
        "Checking for circular reference - Parent: %s, Derived: %s",
        parent_id,
        derived_id,
    )

    def check_ancestors(doc_id: str, target_id: str, visited: set) -> bool:
        """Check if target_id is an ancestor of doc_id."""
        logger.debug(
            "Checking ancestors - Current: %s, Target: %s, Visited: %s", doc_id, target_id, visited
        )

        if doc_id in visited:
            logger.warning(
                "Circular reference detected: %s appears multiple times in ancestor chain",
                doc_id,
            )
            return True

        if doc_id == target_id:
            logger.warning(
                "Circular reference detected: %s is an ancestor",
                target_id,
            )
            return True

        visited.add(doc_id)
        lineage = storage.get_lineage(doc_id)
        if not lineage:
            logger.debug(
                "Document %s not found in lineage tracking, skipping ancestor check", doc_id
            )
            return False

        logger.debug("Checking parents of %s: %s", doc_id, lineage.parents)
        # Check all parents recursively
        for parent_doc_id in lineage.parents:
            if check_ancestors(parent_doc_id, target_id, visited.copy()):
                logger.warning("Found circular reference through parent %s", parent_doc_id)
                return True
        return False

    def check_descendants(doc_id: str, target_id: str, visited: set) -> bool:
        """Check if target_id is a descendant of doc_id."""
        logger.debug(
            "Checking descendants - Current: %s, Target: %s, Visited: %s",
            doc_id,
            target_id,
            visited,
        )

        if doc_id in visited:
            logger.warning(
                "Circular reference detected: %s appears multiple times in descendant chain",
                doc_id,
            )
            return True

        if doc_id == target_id:
            logger.warning(
                "Circular reference detected: %s is a descendant",
                target_id,
            )
            return True

        visited.add(doc_id)
        lineage = storage.get_lineage(doc_id)
        if not lineage:
            logger.debug(
                "Document %s not found in lineage tracking, skipping descendant check", doc_id
            )
            return False

        logger.debug("Checking derived documents of %s: %s", doc_id, lineage.derived_documents)
        # Check all derived documents recursively
        for derived_doc_id in lineage.derived_documents:
            if check_descendants(derived_doc_id, target_id, visited.copy()):
                logger.warning(
                    "Found circular reference through derived document %s", derived_doc_id
                )
                return True
        return False

    try:
        # Check if derived_id is an ancestor of parent_id
        logger.debug("Checking if %s is an ancestor of %s", derived_id, parent_id)
        if check_ancestors(parent_id, derived_id, set()):
            logger.warning(
                "Circular reference detected: %s is an ancestor of %s", derived_id, parent_id
            )
            return True

        # Check if parent_id is a descendant of derived_id
        logger.debug("Checking if %s is a descendant of %s", parent_id, derived_id)
        if check_descendants(derived_id, parent_id, set()):
            logger.warning(
                "Circular reference detected: %s is a descendant of %s", parent_id, derived_id
            )
            return True

        logger.debug("No circular reference detected")
        return False

    except Exception as e:
        logger.error("Error checking for circular reference: %s", str(e))
        raise
