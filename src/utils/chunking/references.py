"""Cross-referencing system for managing relationships between text chunks.

This module provides functionality for creating, managing, and validating
bi-directional references between chunks of text. It supports different types
of references (direct, indirect, structural) and ensures reference integrity.
"""

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4


class ReferenceType(Enum):
    """Types of references between chunks."""

    # Direct references (explicit connections)
    CITATION = "citation"  # Direct quote or citation
    CONTINUATION = "continuation"  # Content continues in another chunk
    LINK = "link"  # Explicit link/reference to another chunk

    # Indirect references (semantic connections)
    RELATED = "related"  # Semantically related content
    SIMILAR = "similar"  # Similar topic or content
    CONTEXT = "context"  # Provides context or background

    # Structural references (document organization)
    PARENT = "parent"  # Parent section or container
    CHILD = "child"  # Child section or subsection
    NEXT = "next"  # Next sequential chunk
    PREVIOUS = "previous"  # Previous sequential chunk
    TOC = "toc"  # Table of contents entry


@dataclass
class Reference:
    """Represents a reference between two chunks."""

    source_id: UUID
    target_id: UUID
    ref_type: ReferenceType
    metadata: dict = field(default_factory=dict)
    bidirectional: bool = True

    def __post_init__(self):
        """Validate reference data."""
        if not isinstance(self.source_id, UUID):
            raise TypeError(f"source_id must be UUID, got {type(self.source_id)}")
        if not isinstance(self.target_id, UUID):
            raise TypeError(f"target_id must be UUID, got {type(self.target_id)}")
        if not isinstance(self.ref_type, ReferenceType):
            raise TypeError(f"ref_type must be ReferenceType, got {type(self.ref_type)}")
        if self.source_id == self.target_id:
            raise ValueError("Self-referential chunks are not allowed")


@dataclass
class ChunkReference:
    """Container for a chunk's content and its references."""

    chunk_id: UUID
    content: str
    references: dict[ReferenceType, set[UUID]] = field(
        default_factory=lambda: {rt: set() for rt in ReferenceType}
    )
    metadata: dict = field(default_factory=dict)

    @property
    def all_references(self) -> set[UUID]:
        """Get all referenced chunk IDs regardless of type."""
        return {ref for refs in self.references.values() for ref in refs}


class ReferenceManager:
    """Manages references between chunks and ensures reference integrity."""

    def __init__(self):
        """Initialize the reference manager."""
        self._chunks: dict[UUID, ChunkReference] = {}
        self._references: dict[tuple[UUID, UUID], Reference] = {}

    def add_chunk(self, content: str, chunk_id: UUID | None = None) -> UUID:
        """Add a new chunk to the reference system.

        Args:
            content: The text content of the chunk
            chunk_id: Optional UUID for the chunk. If not provided, one will be generated.

        Returns:
            The UUID of the added chunk

        Raises:
            ValueError: If chunk_id already exists
        """
        chunk_id = chunk_id or uuid4()
        if chunk_id in self._chunks:
            raise ValueError(f"Chunk with ID {chunk_id} already exists")

        self._chunks[chunk_id] = ChunkReference(chunk_id=chunk_id, content=content)
        return chunk_id

    def add_reference(
        self,
        source_id: UUID,
        target_id: UUID,
        ref_type: ReferenceType,
        metadata: dict | None = None,
        bidirectional: bool = True,
    ) -> None:
        """Add a reference between two chunks.

        Args:
            source_id: UUID of the source chunk
            target_id: UUID of the target chunk
            ref_type: Type of reference to create
            metadata: Optional metadata for the reference
            bidirectional: Whether to create a bidirectional reference

        Raises:
            ValueError: If either chunk doesn't exist or reference is invalid
            TypeError: If parameters are of wrong type
        """
        # Validate chunks exist
        if source_id not in self._chunks:
            raise ValueError(f"Source chunk {source_id} does not exist")
        if target_id not in self._chunks:
            raise ValueError(f"Target chunk {target_id} does not exist")

        # Create reference
        ref = Reference(
            source_id=source_id,
            target_id=target_id,
            ref_type=ref_type,
            metadata=metadata or {},
            bidirectional=bidirectional,
        )

        # Add to references
        self._references[source_id, target_id] = ref
        self._chunks[source_id].references[ref_type].add(target_id)

        # Add reverse reference if bidirectional
        if bidirectional:
            reverse_type = self._get_reverse_reference_type(ref_type)
            self._references[target_id, source_id] = Reference(
                source_id=target_id,
                target_id=source_id,
                ref_type=reverse_type,
                metadata=metadata or {},
                bidirectional=True,
            )
            self._chunks[target_id].references[reverse_type].add(source_id)

    def get_references(self, chunk_id: UUID, ref_type: ReferenceType | None = None) -> set[UUID]:
        """Get all references of a specific type for a chunk.

        Args:
            chunk_id: The UUID of the chunk to get references for
            ref_type: Optional reference type to filter by

        Returns:
            Set of chunk IDs that are referenced

        Raises:
            ValueError: If chunk doesn't exist
        """
        if chunk_id not in self._chunks:
            raise ValueError(f"Chunk {chunk_id} does not exist")

        chunk = self._chunks[chunk_id]
        if ref_type:
            return chunk.references.get(ref_type, set())
        return chunk.all_references

    def remove_reference(
        self, source_id: UUID, target_id: UUID, ref_type: ReferenceType | None = None
    ) -> None:
        """Remove a reference between chunks.

        Args:
            source_id: UUID of the source chunk
            target_id: UUID of the target chunk
            ref_type: Optional specific reference type to remove

        Raises:
            ValueError: If reference doesn't exist
        """
        if (source_id, target_id) not in self._references:
            raise ValueError(f"No reference exists between {source_id} and {target_id}")

        ref = self._references[source_id, target_id]
        if ref_type and ref.ref_type != ref_type:
            raise ValueError(f"Reference of type {ref_type} does not exist")

        # Remove reference
        del self._references[source_id, target_id]
        self._chunks[source_id].references[ref.ref_type].remove(target_id)

        # Remove reverse reference if bidirectional
        if ref.bidirectional and (target_id, source_id) in self._references:
            reverse_ref = self._references[target_id, source_id]
            del self._references[target_id, source_id]
            self._chunks[target_id].references[reverse_ref.ref_type].remove(source_id)

    def validate_references(self) -> list[str]:
        """Validate all references and return any issues found.

        Returns:
            List of validation error messages
        """
        issues = []

        # Check for orphaned references
        for (source_id, target_id), ref in self._references.items():
            if source_id not in self._chunks:
                issues.append(f"Reference from non-existent chunk {source_id}")
            if target_id not in self._chunks:
                issues.append(f"Reference to non-existent chunk {target_id}")

        # Check for broken bidirectional references
        for (source_id, target_id), ref in self._references.items():
            if ref.bidirectional and (target_id, source_id) not in self._references:
                issues.append(f"Missing reverse reference from {target_id} to {source_id}")

        return issues

    @staticmethod
    def _get_reverse_reference_type(ref_type: ReferenceType) -> ReferenceType:
        """Get the appropriate reverse reference type."""
        reverse_types = {
            ReferenceType.PARENT: ReferenceType.CHILD,
            ReferenceType.CHILD: ReferenceType.PARENT,
            ReferenceType.NEXT: ReferenceType.PREVIOUS,
            ReferenceType.PREVIOUS: ReferenceType.NEXT,
        }
        return reverse_types.get(ref_type, ref_type)
