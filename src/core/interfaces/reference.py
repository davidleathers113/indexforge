"""Core reference management interfaces.

This module defines the interfaces for managing references between chunks
and documents. It provides protocols for reference management, validation,
and semantic relationship operations.
"""

from typing import TYPE_CHECKING, Any, Optional, Protocol, TypeVar
from uuid import UUID


if TYPE_CHECKING:
    import numpy as np

    from src.core.models.references import Reference, ReferenceType
    from src.core.settings import Settings

T = TypeVar("T", bound="Reference")


class ReferenceValidator(Protocol):
    """Protocol for reference validation operations."""

    def validate_reference(self, ref: "Reference") -> list[str]:
        """Validate a single reference.

        Args:
            ref (Reference): Reference to validate

        Returns:
            List[str]: List of validation error messages, empty if valid

        Raises:
            ValueError: If reference is malformed
        """
        ...

    def validate_references(self, refs: list["Reference"]) -> list[str]:
        """Validate multiple references.

        Args:
            refs (List[Reference]): References to validate

        Returns:
            List[str]: List of validation error messages, empty if all valid

        Raises:
            ValueError: If any reference is malformed
        """
        ...


class ReferenceManager(Protocol):
    """Protocol for reference management operations."""

    def __init__(self, settings: "Settings") -> None:
        """Initialize the reference manager.

        Args:
            settings (Settings): Application settings
        """
        ...

    def add_reference(
        self,
        source_id: UUID,
        target_id: UUID,
        ref_type: "ReferenceType",
        metadata: dict[str, Any] | None = None,
        bidirectional: bool = False,
    ) -> T:
        """Add a reference between chunks.

        Args:
            source_id (UUID): ID of the source chunk
            target_id (UUID): ID of the target chunk
            ref_type (ReferenceType): Type of reference
            metadata (Optional[Dict[str, Any]], optional): Reference metadata. Defaults to None.
            bidirectional (bool, optional): Whether to create bidirectional reference.
                Defaults to False.

        Returns:
            T: Created reference

        Raises:
            ServiceStateError: If manager is not initialized
            ValueError: If source_id or target_id is invalid
        """
        ...

    def get_references(
        self,
        chunk_id: UUID,
        ref_type: Optional["ReferenceType"] = None,
        include_metadata: bool = False,
    ) -> list[T]:
        """Get references for a chunk.

        Args:
            chunk_id (UUID): ID of the chunk
            ref_type (Optional[ReferenceType], optional): Filter by reference type.
                Defaults to None.
            include_metadata (bool, optional): Whether to include reference metadata.
                Defaults to False.

        Returns:
            List[T]: List of references matching the criteria

        Raises:
            ServiceStateError: If manager is not initialized
            ValueError: If chunk_id is invalid
        """
        ...

    def remove_reference(self, ref: T) -> None:
        """Remove a reference.

        Args:
            ref (T): Reference to remove

        Raises:
            ServiceStateError: If manager is not initialized
            ValueError: If reference does not exist
        """
        ...

    def validate_references(self) -> list[str]:
        """Validate all references.

        Returns:
            List[str]: List of validation error messages, empty if all valid

        Raises:
            ServiceStateError: If manager is not initialized
        """
        ...


class SemanticReferenceManager(Protocol):
    """Protocol for semantic reference management operations."""

    def __init__(self, settings: "Settings") -> None:
        """Initialize the semantic reference manager.

        Args:
            settings (Settings): Application settings
        """
        ...

    def add_chunk_embedding(self, chunk_id: UUID, embedding: "np.ndarray") -> None:
        """Add a chunk embedding.

        Args:
            chunk_id (UUID): ID of the chunk
            embedding (np.ndarray): Vector embedding of chunk content

        Raises:
            ServiceStateError: If manager is not initialized
            ValueError: If chunk_id is invalid or embedding has wrong shape
        """
        ...

    def establish_semantic_references(
        self,
        similarity_threshold: float = 0.8,
        max_refs_per_chunk: int = 3,
    ) -> list[T]:
        """Establish semantic references between chunks.

        Args:
            similarity_threshold (float, optional): Minimum similarity score (0-1).
                Defaults to 0.8.
            max_refs_per_chunk (int, optional): Maximum references per chunk.
                Defaults to 3.

        Returns:
            List[T]: List of created references

        Raises:
            ServiceStateError: If manager is not initialized
            ValueError: If similarity_threshold not in [0,1] or max_refs_per_chunk < 1
        """
        ...

    def establish_topic_references(
        self,
        n_topics: int = 5,
        min_chunks_per_topic: int = 3,
    ) -> tuple[list[T], dict[int, list[UUID]]]:
        """Establish topic-based references between chunks.

        Args:
            n_topics (int, optional): Number of topics for clustering. Defaults to 5.
            min_chunks_per_topic (int, optional): Minimum chunks per topic.
                Defaults to 3.

        Returns:
            Tuple[List[T], Dict[int, List[UUID]]]: Tuple containing:
                - List of created references
                - Dictionary mapping topic IDs to lists of chunk UUIDs

        Raises:
            ServiceStateError: If manager is not initialized
            ValueError: If n_topics < 1 or min_chunks_per_topic < 1
        """
        ...
