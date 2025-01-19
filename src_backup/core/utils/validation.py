"""Core validation utilities.

This module provides utility functions for validating references, chunks,
and documents. It includes functions for detecting circular references,
validating relationships, and ensuring data integrity.
"""

from uuid import UUID

from src.core.models.chunks import Chunk
from src.core.models.documents import Document
from src.core.models.references import Reference


def detect_circular_references(
    references: dict[UUID, list[Reference]], start_id: UUID, visited: set[UUID] | None = None
) -> list[str]:
    """Detect circular references in a reference graph.

    Args:
        references: Dictionary mapping chunk IDs to their references
        start_id: Starting chunk ID for detection
        visited: Set of visited chunk IDs (for recursive calls)

    Returns:
        List of error messages describing circular references
    """
    errors = []
    if visited is None:
        visited = set()

    if start_id in visited:
        cycle = " -> ".join(
            str(id) for id in list(visited)[list(visited).index(start_id) :] + [start_id]
        )
        errors.append(f"Circular reference detected: {cycle}")
        return errors

    visited.add(start_id)
    if start_id in references:
        for ref in references[start_id]:
            errors.extend(detect_circular_references(references, ref.target_id, visited.copy()))

    return errors


def validate_chunk_references(chunk: Chunk, all_chunks: dict[UUID, Chunk]) -> list[str]:
    """Validate references for a chunk.

    Args:
        chunk: Chunk to validate
        all_chunks: Dictionary of all available chunks

    Returns:
        List of validation error messages
    """
    errors = []

    for ref in chunk.references:
        # Validate target exists
        if ref.target_id not in all_chunks:
            errors.append(f"Reference target {ref.target_id} not found")
            continue

        # Validate bidirectional references
        if ref.bidirectional:
            target = all_chunks[ref.target_id]
            has_back_ref = any(
                back_ref.target_id == chunk.id and back_ref.ref_type == ref.ref_type
                for back_ref in target.references
            )
            if not has_back_ref:
                errors.append(
                    f"Missing back-reference from {ref.target_id} to {chunk.id} "
                    f"for type {ref.ref_type}"
                )

    return errors


def validate_document_relationships(doc: Document, all_docs: dict[UUID, Document]) -> list[str]:
    """Validate relationships for a document.

    Args:
        doc: Document to validate
        all_docs: Dictionary of all available documents

    Returns:
        List of validation error messages
    """
    errors = []

    # Validate parent reference
    if doc.parent_id is not None:
        if doc.parent_id not in all_docs:
            errors.append(f"Parent document {doc.parent_id} not found")
        elif doc.id not in all_docs[doc.parent_id].child_ids:
            errors.append(
                f"Inconsistent parent-child relationship: {doc.parent_id} does not list "
                f"{doc.id} as child"
            )

    # Validate child references
    for child_id in doc.child_ids:
        if child_id not in all_docs:
            errors.append(f"Child document {child_id} not found")
        else:
            child = all_docs[child_id]
            if child.parent_id != doc.id:
                errors.append(
                    f"Inconsistent parent-child relationship: {child_id} lists "
                    f"{child.parent_id} as parent instead of {doc.id}"
                )

    return errors


def validate_reference_integrity(
    chunks: dict[UUID, Chunk], docs: dict[UUID, Document]
) -> list[str]:
    """Validate overall reference integrity.

    Args:
        chunks: Dictionary of all chunks
        docs: Dictionary of all documents

    Returns:
        List of validation error messages
    """
    errors = []

    # Build reference graph
    ref_graph = {chunk_id: chunk.references for chunk_id, chunk in chunks.items()}

    # Check for circular references
    for chunk_id in chunks:
        errors.extend(detect_circular_references(ref_graph, chunk_id))

    # Validate chunk references
    for chunk in chunks.values():
        errors.extend(validate_chunk_references(chunk, chunks))

    # Validate document relationships
    for doc in docs.values():
        errors.extend(validate_document_relationships(doc, docs))

    return errors
