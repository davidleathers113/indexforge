"""Reference storage service implementation."""

from typing import Dict, List, Set, TypeVar
from uuid import UUID

from src.core.errors import ServiceStateError
from src.core.interfaces.storage import ReferenceStorage
from src.core.models.references import Reference
from src.services.base import BaseService
from src.services.storage.metrics import StorageMetricsService

R = TypeVar("R", bound=Reference)


class ReferenceStorageService(ReferenceStorage, BaseService):
    """Implementation of reference storage operations."""

    def __init__(self, metrics: StorageMetricsService) -> None:
        """Initialize reference storage.

        Args:
            metrics: Storage metrics service
        """
        BaseService.__init__(self)
        self._references: Dict[UUID, Set[R]] = {}  # chunk_id -> set of references
        self._metrics = metrics
        self._initialized = True

    def store_reference(self, ref: R) -> None:
        """Store a reference.

        Args:
            ref: Reference to store

        Raises:
            ServiceStateError: If storage is not initialized
            ValueError: If reference is invalid
        """
        if not self.is_initialized:
            raise ServiceStateError("Reference storage is not initialized")

        if not ref:
            raise ValueError("Reference cannot be None")

        if ref.source_id not in self._references:
            self._references[ref.source_id] = set()

        # Check if reference already exists to avoid double counting
        if ref not in self._references[ref.source_id]:
            self._references[ref.source_id].add(ref)
            self._metrics.increment_storage_stat("reference_count")
            self._metrics.increment_storage_stat("total_bytes", len(str(ref).encode()))
            self._metrics.increment_operation_count("writes")

    def get_references(self, chunk_id: UUID) -> List[R]:
        """Get references for a chunk.

        Args:
            chunk_id: Chunk ID

        Returns:
            List[R]: List of references associated with the chunk

        Raises:
            ServiceStateError: If storage is not initialized
        """
        if not self.is_initialized:
            raise ServiceStateError("Reference storage is not initialized")

        self._metrics.increment_operation_count("reads")
        return list(self._references.get(chunk_id, set()))

    def delete_reference(self, ref: R) -> None:
        """Delete a reference.

        Args:
            ref: Reference to delete

        Raises:
            ServiceStateError: If storage is not initialized
            KeyError: If reference does not exist
        """
        if not self.is_initialized:
            raise ServiceStateError("Reference storage is not initialized")

        if ref.source_id not in self._references:
            raise KeyError(f"No references found for chunk {ref.source_id}")

        if ref not in self._references[ref.source_id]:
            raise KeyError(f"Reference {ref} does not exist")

        ref_size = len(str(ref).encode())
        self._references[ref.source_id].remove(ref)

        # Clean up empty sets
        if not self._references[ref.source_id]:
            del self._references[ref.source_id]

        self._metrics.decrement_storage_stat("reference_count")
        self._metrics.decrement_storage_stat("total_bytes", ref_size)
        self._metrics.increment_operation_count("deletes")
