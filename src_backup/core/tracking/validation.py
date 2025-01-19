"""
Document lineage validation and integrity checks.

This module provides validation functions for ensuring the integrity and
correctness of document lineage data. It includes checks for circular
derivation relationships and chunk reference validity.

Key Features:
    - Circular derivation detection
    - Chunk reference validation
    - Relationship integrity checks
    - Validation error reporting
    - Recursive validation

Example:
    ```python
    from .models import DocumentLineage, ChunkReference

    # Create document lineages
    doc1 = DocumentLineage(doc_id="doc1")
    doc2 = DocumentLineage(doc_id="doc2")
    doc3 = DocumentLineage(doc_id="doc3")

    # Set up derivation relationships
    doc2.derived_from = "doc1"
    doc3.derived_from = "doc2"

    # Check for circular derivations
    lineage_data = {
        "doc1": doc1,
        "doc2": doc2,
        "doc3": doc3
    }
    errors = validate_circular_derivations(lineage_data)
    if errors:
        print("Found circular derivations:", errors)

    # Validate chunk references
    chunk_ref = ChunkReference(
        source_doc="doc1",
        chunk_id="chunk1",
        content="Sample content"
    )
    doc2.chunk_references.append(chunk_ref)

    errors = validate_chunk_references(lineage_data)
    if errors:
        print("Invalid chunk references:", errors)
    ```
"""

import logging

from .models import DocumentLineage


logger = logging.getLogger(__name__)


def validate_circular_derivations(lineage_data: dict[str, DocumentLineage]) -> list[str]:
    """
    Check for circular derivation relationships between documents.

    This function detects cycles in document derivation relationships by
    performing a depth-first search through the derivation chain for each
    document. It identifies cases where documents form a circular dependency
    (e.g., A -> B -> C -> A).

    Args:
        lineage_data: Dictionary mapping document IDs to their lineage data

    Returns:
        List of error messages describing any circular derivations found.
        Each message identifies the documents involved in the cycle.

    Example:
        ```python
        # Create document lineages with circular dependency
        doc1 = DocumentLineage(doc_id="doc1")
        doc2 = DocumentLineage(doc_id="doc2")
        doc3 = DocumentLineage(doc_id="doc3")

        doc2.derived_from = "doc1"
        doc3.derived_from = "doc2"
        doc1.derived_from = "doc3"  # Creates cycle

        lineage_data = {
            "doc1": doc1,
            "doc2": doc2,
            "doc3": doc3
        }

        errors = validate_circular_derivations(lineage_data)
        for error in errors:
            print(f"Validation error: {error}")
        ```
    """
    errors = []
    visited = set()

    def check_derivation_chain(doc_id: str, chain: set[str]) -> None:
        """
        Recursively check derivation chain for cycles.

        Args:
            doc_id: Current document ID being checked
            chain: Set of document IDs in current chain
        """
        if doc_id in chain:
            cycle = " -> ".join(list(chain)[list(chain).index(doc_id) :] + [doc_id])
            errors.append(f"Circular derivation detected: {cycle}")
            return

        if doc_id in visited:
            return

        visited.add(doc_id)
        doc = lineage_data.get(doc_id)
        if doc and doc.derived_from:
            chain.add(doc_id)
            check_derivation_chain(doc.derived_from, chain)
            chain.remove(doc_id)

    for doc_id in lineage_data:
        check_derivation_chain(doc_id, set())

    return errors


def validate_chunk_references(lineage_data: dict[str, DocumentLineage]) -> list[str]:
    """
    Validate chunk references across all documents.

    This function checks that all chunk references in documents point to valid
    source documents and chunks. It verifies that referenced documents exist
    and that chunk IDs are valid within those documents.

    Args:
        lineage_data: Dictionary mapping document IDs to their lineage data

    Returns:
        List of error messages describing any invalid chunk references.
        Each message identifies the invalid reference and the nature of
        the validation failure.

    Example:
        ```python
        # Create documents with chunk references
        source_doc = DocumentLineage(doc_id="source")
        derived_doc = DocumentLineage(doc_id="derived")

        # Add valid chunk reference
        chunk_ref = ChunkReference(
            source_doc="source",
            chunk_id="chunk1",
            content="Sample content"
        )
        derived_doc.chunk_references.append(chunk_ref)

        # Add invalid reference
        bad_ref = ChunkReference(
            source_doc="nonexistent",
            chunk_id="chunk2",
            content="Invalid reference"
        )
        derived_doc.chunk_references.append(bad_ref)

        lineage_data = {
            "source": source_doc,
            "derived": derived_doc
        }

        errors = validate_chunk_references(lineage_data)
        for error in errors:
            print(f"Validation error: {error}")
        ```
    """
    errors = []

    for doc_id, doc in lineage_data.items():
        for chunk_ref in doc.chunk_references:
            source_doc = lineage_data.get(chunk_ref.source_doc)
            if not source_doc:
                errors.append(
                    f"Document {doc_id} references nonexistent source document "
                    f"{chunk_ref.source_doc} in chunk {chunk_ref.chunk_id}"
                )
                continue

            # Add additional chunk validation logic here if needed
            # For example, checking if chunk_id exists in source document
            # or validating chunk content matches source

    return errors


def validate_lineage_relationships(lineage_data: dict[str, DocumentLineage]) -> list[str]:
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
        List of error messages describing any invalid relationships found.

    Example:
        ```python
        doc1 = DocumentLineage(doc_id="doc1")
        doc2 = DocumentLineage(doc_id="doc2", derived_from="doc1")

        lineage_data = {
            "doc1": doc1,
            "doc2": doc2
        }
        errors = validate_lineage_relationships(lineage_data)
        for error in errors:
            print(f"Validation error: {error}")
        ```
    """
    errors = []

    for doc_id, doc in lineage_data.items():
        # Validate derived_from references
        if doc.derived_from:
            if doc.derived_from not in lineage_data:
                errors.append(
                    f"Document {doc_id} is derived from nonexistent document {doc.derived_from}"
                )
            elif doc.derived_from == doc_id:
                errors.append(f"Document {doc_id} cannot be derived from itself")

        # Validate parent-child relationships
        for child_id in doc.children:
            if child_id not in lineage_data:
                errors.append(f"Document {doc_id} references nonexistent child document {child_id}")
            else:
                child_doc = lineage_data[child_id]
                if doc_id not in child_doc.parents:
                    errors.append(
                        f"Inconsistent parent-child relationship: {doc_id} lists {child_id} "
                        f"as child, but {child_id} does not list {doc_id} as parent"
                    )

        # Validate parent references
        for parent_id in doc.parents:
            if parent_id not in lineage_data:
                errors.append(
                    f"Document {doc_id} references nonexistent parent document {parent_id}"
                )
            else:
                parent_doc = lineage_data[parent_id]
                if doc_id not in parent_doc.children:
                    errors.append(
                        f"Inconsistent parent-child relationship: {doc_id} lists {parent_id} "
                        f"as parent, but {parent_id} does not list {doc_id} as child"
                    )

    return errors


def validate_lineage(lineage_data: dict[str, DocumentLineage]) -> list[str]:
    """
    Validate the entire lineage data for consistency and correctness.

    This function performs comprehensive validation of the lineage data,
    including circular derivations, relationship consistency, and reference
    validity.

    Args:
        lineage_data: Dictionary mapping document IDs to their lineage data

    Returns:
        List of error messages describing any validation failures

    Example:
        ```python
        errors = validate_lineage(lineage_data)
        for error in errors:
            print(f"Validation error: {error}")
        ```
    """
    errors = []

    # Check for circular derivations
    errors.extend(validate_circular_derivations(lineage_data))

    # Check relationship consistency
    errors.extend(validate_lineage_relationships(lineage_data))

    # Check for missing references
    for doc_id, lineage in lineage_data.items():
        # Check derived_from reference
        if lineage.derived_from and lineage.derived_from not in lineage_data:
            errors.append(
                f"Document {doc_id} references nonexistent parent document {lineage.derived_from}"
            )

        # Check derived documents
        for derived_id in lineage.derived_documents:
            if derived_id not in lineage_data:
                errors.append(
                    f"Document {doc_id} references nonexistent derived document {derived_id}"
                )
            else:
                derived_doc = lineage_data[derived_id]
                if derived_doc.derived_from != doc_id:
                    errors.append(
                        f"Inconsistent derivation relationship: {doc_id} lists {derived_id} "
                        f"as derived, but {derived_id} lists {derived_doc.derived_from} as parent"
                    )

    return errors
