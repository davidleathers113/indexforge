"""Core reference management interfaces.

This module defines the interfaces for managing references between chunks
and documents. It provides abstract base classes for reference management,
validation, and processing.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Tuple
from uuid import UUID

from src.core.models.references import Reference, ReferenceType


class ReferenceValidator(Protocol):
    """Protocol for reference validation."""

    def validate_reference(self, ref: Reference) -> List[str]:
        """Validate a single reference.

        Args:
            ref: Reference to validate

        Returns:
            List of validation error messages
        """
        ...

    def validate_references(self, refs: List[Reference]) -> List[str]:
        """Validate multiple references.

        Args:
            refs: References to validate

        Returns:
            List of validation error messages
        """
        ...


class ReferenceManager(ABC):
    """Interface for reference management."""

    @abstractmethod
    def add_reference(
        self,
        source_id: UUID,
        target_id: UUID,
        ref_type: ReferenceType,
        metadata: Optional[Dict] = None,
        bidirectional: bool = False,
    ) -> Reference:
        """Add a reference between chunks.

        Args:
            source_id: ID of the source chunk
            target_id: ID of the target chunk
            ref_type: Type of reference
            metadata: Optional reference metadata
            bidirectional: Whether to create bidirectional reference

        Returns:
            Created reference
        """
        pass

    @abstractmethod
    def get_references(
        self,
        chunk_id: UUID,
        ref_type: Optional[ReferenceType] = None,
        include_metadata: bool = False,
    ) -> List[Reference]:
        """Get references for a chunk.

        Args:
            chunk_id: ID of the chunk
            ref_type: Optional filter by reference type
            include_metadata: Whether to include reference metadata

        Returns:
            List of references
        """
        pass

    @abstractmethod
    def remove_reference(self, ref: Reference) -> None:
        """Remove a reference.

        Args:
            ref: Reference to remove
        """
        pass

    @abstractmethod
    def validate_references(self) -> List[str]:
        """Validate all references.

        Returns:
            List of validation error messages
        """
        pass


class SemanticReferenceManager(ReferenceManager):
    """Interface for semantic reference management."""

    @abstractmethod
    def add_chunk_embedding(self, chunk_id: UUID, embedding: Any) -> None:
        """Add a chunk embedding.

        Args:
            chunk_id: ID of the chunk
            embedding: Vector embedding of chunk content (numpy.ndarray)
        """
        pass

    @abstractmethod
    def establish_semantic_references(
        self,
        similarity_threshold: float = 0.8,
        max_refs_per_chunk: int = 3,
    ) -> List[Reference]:
        """Establish semantic references between chunks.

        Args:
            similarity_threshold: Minimum similarity score (0-1)
            max_refs_per_chunk: Maximum references per chunk

        Returns:
            List of created references
        """
        pass

    @abstractmethod
    def establish_topic_references(
        self,
        n_topics: int = 5,
        min_chunks_per_topic: int = 3,
    ) -> Tuple[List[Reference], Dict[int, List[UUID]]]:
        """Establish topic-based references between chunks.

        Args:
            n_topics: Number of topics for clustering
            min_chunks_per_topic: Minimum chunks per topic

        Returns:
            Tuple of (created references, topic assignments)
        """
        pass
