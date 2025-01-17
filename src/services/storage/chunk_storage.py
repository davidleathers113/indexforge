"""Chunk storage service implementation.

This module provides a concrete implementation of the chunk storage interface
with support for batch operations, metrics collection, and memory management.
"""

from typing import TypeVar
from uuid import UUID, uuid4

from src.core.interfaces.metrics import MetricsProvider, StorageMetrics
from src.core.interfaces.storage import ChunkStorage
from src.core.models.chunks import Chunk, ChunkMetadata
from src.core.settings import Settings

from .base import BaseStorageService, BatchConfig, BatchResult


C = TypeVar("C", bound=Chunk)


class ChunkStorageService(BaseStorageService, ChunkStorage[C]):
    """Implementation of chunk storage operations with metrics and batch support."""

    def __init__(
        self,
        settings: Settings,
        metrics: StorageMetrics | None = None,
        metrics_provider: MetricsProvider | None = None,
        batch_config: BatchConfig | None = None,
    ) -> None:
        """Initialize chunk storage.

        Args:
            settings: Application settings
            metrics: Optional storage metrics collector
            metrics_provider: Optional metrics provider for detailed metrics
            batch_config: Optional batch operation configuration
        """
        super().__init__(
            metrics=metrics, metrics_provider=metrics_provider, batch_config=batch_config
        )
        self._chunks: dict[UUID, C] = {}
        self._settings = settings

    def store_chunk(self, chunk: C) -> UUID:
        """Store a chunk.

        Args:
            chunk: Chunk to store

        Returns:
            UUID: Generated chunk ID

        Raises:
            ValueError: If chunk is invalid
        """
        if not chunk:
            raise ValueError("Chunk cannot be None")

        self._time_operation("store_chunk")
        try:
            chunk_id = uuid4()
            self._chunks[chunk_id] = chunk
            self._record_operation("store")
            return chunk_id
        finally:
            self._stop_timing("store_chunk")

    def get_chunk(self, chunk_id: UUID) -> C:
        """Retrieve a chunk by ID.

        Args:
            chunk_id: ID of chunk to retrieve

        Returns:
            C: Retrieved chunk

        Raises:
            KeyError: If chunk does not exist
        """
        self._time_operation("get_chunk")
        try:
            if chunk_id not in self._chunks:
                raise KeyError(f"Chunk {chunk_id} not found")

            chunk = self._chunks[chunk_id]
            self._record_operation("get")
            return chunk
        finally:
            self._stop_timing("get_chunk")

    def update_chunk(self, chunk_id: UUID, chunk: C) -> None:
        """Update a chunk.

        Args:
            chunk_id: ID of chunk to update
            chunk: Updated chunk

        Raises:
            ValueError: If chunk is invalid
            KeyError: If chunk does not exist
        """
        if not chunk:
            raise ValueError("Chunk cannot be None")

        self._time_operation("update_chunk")
        try:
            if chunk_id not in self._chunks:
                raise KeyError(f"Chunk {chunk_id} not found")

            self._chunks[chunk_id] = chunk
            self._record_operation("update")
        finally:
            self._stop_timing("update_chunk")

    def delete_chunk(self, chunk_id: UUID) -> None:
        """Delete a chunk.

        Args:
            chunk_id: ID of chunk to delete

        Raises:
            KeyError: If chunk does not exist
        """
        self._time_operation("delete_chunk")
        try:
            if chunk_id not in self._chunks:
                raise KeyError(f"Chunk {chunk_id} not found")

            del self._chunks[chunk_id]
            self._record_operation("delete")
        finally:
            self._stop_timing("delete_chunk")

    def batch_store_chunks(self, chunks: list[C]) -> BatchResult[C]:
        """Store multiple chunks in a batch operation.

        Args:
            chunks: List of chunks to store

        Returns:
            BatchResult containing successful and failed chunks
        """
        return self.process_batch(chunks, "store_chunk")

    def batch_update_chunks(self, updates: list[tuple[UUID, C]]) -> BatchResult[tuple[UUID, C]]:
        """Update multiple chunks in a batch operation.

        Args:
            updates: List of (chunk_id, chunk) pairs to update

        Returns:
            BatchResult containing successful and failed updates
        """
        return self.process_batch(updates, "update_chunk")

    def check_health(self) -> tuple[bool, str]:
        """Check the health of the chunk storage service.

        Returns:
            Tuple containing:
                - bool: True if service is healthy
                - str: Status message
        """
        try:
            # Perform basic health check
            metadata = ChunkMetadata(
                content_type="text",
                language="en",
                line_numbers=(1, 1),
            )
            test_chunk = Chunk(
                content="health check content",
                metadata=metadata,
            )
            chunk_id = self.store_chunk(test_chunk)
            self.delete_chunk(chunk_id)
            return True, "Chunk storage service is healthy"
        except Exception as e:
            return False, f"Chunk storage health check failed: {e!s}"
