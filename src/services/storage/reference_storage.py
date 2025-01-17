"""Reference storage service implementation.

This module provides a concrete implementation of the reference storage interface
with support for batch operations, metrics collection, and memory management.
"""

from typing import Dict, List, Optional, Set, TypeVar
from uuid import UUID

from src.core.interfaces.metrics import MetricsProvider, StorageMetrics
from src.core.interfaces.storage import ReferenceStorage
from src.core.models.references import Reference
from src.core.settings import Settings

from .base import BaseStorageService, BatchConfig, BatchResult

R = TypeVar("R", bound=Reference)


class ReferenceStorageService(BaseStorageService, ReferenceStorage[R]):
    """Implementation of reference storage operations with metrics and batch support."""

    def __init__(
        self,
        settings: Settings,
        metrics: Optional[StorageMetrics] = None,
        metrics_provider: Optional[MetricsProvider] = None,
        batch_config: Optional[BatchConfig] = None,
    ) -> None:
        """Initialize reference storage.

        Args:
            settings: Application settings
            metrics: Optional storage metrics collector
            metrics_provider: Optional metrics provider for detailed metrics
            batch_config: Optional batch operation configuration
        """
        super().__init__(
            metrics=metrics, metrics_provider=metrics_provider, batch_config=batch_config
        )
        self._references: Dict[UUID, Set[R]] = {}
        self._settings = settings

    def store_reference(self, ref: R) -> None:
        """Store a reference.

        Args:
            ref: Reference to store

        Raises:
            ValueError: If reference is invalid
        """
        if not ref:
            raise ValueError("Reference cannot be None")

        self._time_operation("store_reference")
        try:
            if ref.source_id not in self._references:
                self._references[ref.source_id] = set()
            self._references[ref.source_id].add(ref)
            self._record_operation("store")
        finally:
            self._stop_timing("store_reference")

    def get_references(self, chunk_id: UUID) -> List[R]:
        """Get references for a chunk.

        Args:
            chunk_id: ID of chunk to get references for

        Returns:
            List[R]: List of references associated with the chunk
        """
        self._time_operation("get_references")
        try:
            refs = self._references.get(chunk_id, set())
            self._record_operation("get")
            return list(refs)
        finally:
            self._stop_timing("get_references")

    def delete_reference(self, ref: R) -> None:
        """Delete a reference.

        Args:
            ref: Reference to delete

        Raises:
            KeyError: If reference does not exist
        """
        self._time_operation("delete_reference")
        try:
            if ref.source_id not in self._references:
                raise KeyError(f"No references found for chunk {ref.source_id}")

            refs = self._references[ref.source_id]
            if ref not in refs:
                raise KeyError(f"Reference {ref} not found")

            refs.remove(ref)
            if not refs:
                del self._references[ref.source_id]
            self._record_operation("delete")
        finally:
            self._stop_timing("delete_reference")

    def batch_store_references(self, references: List[R]) -> BatchResult[R]:
        """Store multiple references in a batch operation.

        Args:
            references: List of references to store

        Returns:
            BatchResult containing successful and failed references
        """
        return self.process_batch(references, "store_reference")

    def batch_delete_references(self, references: List[R]) -> BatchResult[R]:
        """Delete multiple references in a batch operation.

        Args:
            references: List of references to delete

        Returns:
            BatchResult containing successful and failed deletions
        """
        return self.process_batch(references, "delete_reference")

    def check_health(self) -> tuple[bool, str]:
        """Check the health of the reference storage service.

        Returns:
            Tuple containing:
                - bool: True if service is healthy
                - str: Status message
        """
        try:
            # Perform basic health check
            test_ref = Reference(
                source_id=UUID("00000000-0000-0000-0000-000000000001"),
                target_id=UUID("00000000-0000-0000-0000-000000000002"),
                ref_type="test",
                confidence=1.0,
            )
            self.store_reference(test_ref)
            self.delete_reference(test_ref)
            return True, "Reference storage service is healthy"
        except Exception as e:
            return False, f"Reference storage health check failed: {str(e)}"
