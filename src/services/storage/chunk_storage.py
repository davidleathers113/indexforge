"""Chunk storage service implementation."""

from typing import Dict, Optional, TypeVar
from uuid import UUID, uuid4

from src.core.errors import ServiceStateError
from src.core.interfaces.storage import ChunkStorage
from src.core.models.chunks import Chunk
from src.services.base import BaseService
from src.services.storage.metrics import StorageMetricsService

C = TypeVar("C", bound=Chunk)


class ChunkStorageService(ChunkStorage, BaseService):
    """Implementation of chunk storage operations."""

    def __init__(self, metrics: StorageMetricsService) -> None:
        """Initialize chunk storage.

        Args:
            metrics: Storage metrics service
        """
        BaseService.__init__(self)
        self._chunks: Dict[UUID, C] = {}
        self._metrics = metrics
        self._initialized = True

    def store_chunk(self, chunk: C) -> UUID:
        """Store a chunk.

        Args:
            chunk: Chunk to store

        Returns:
            UUID: Generated chunk ID

        Raises:
            ServiceStateError: If storage is not initialized
            ValueError: If chunk is invalid
        """
        if not self.is_initialized:
            raise ServiceStateError("Chunk storage is not initialized")

        if not chunk:
            raise ValueError("Chunk cannot be None")

        chunk_id = uuid4()
        self._chunks[chunk_id] = chunk
        self._metrics.increment_storage_stat("chunk_count")
        self._metrics.increment_storage_stat("total_bytes", len(str(chunk).encode()))
        self._metrics.increment_operation_count("writes")
        return chunk_id

    def get_chunk(self, chunk_id: UUID) -> Optional[C]:
        """Get a chunk by ID.

        Args:
            chunk_id: Chunk ID

        Returns:
            Optional[C]: Chunk if found, None otherwise

        Raises:
            ServiceStateError: If storage is not initialized
        """
        if not self.is_initialized:
            raise ServiceStateError("Chunk storage is not initialized")

        self._metrics.increment_operation_count("reads")
        return self._chunks.get(chunk_id)

    def update_chunk(self, chunk_id: UUID, chunk: C) -> None:
        """Update a chunk.

        Args:
            chunk_id: Chunk ID
            chunk: Updated chunk

        Raises:
            ServiceStateError: If storage is not initialized
            ValueError: If chunk is invalid
            KeyError: If chunk does not exist
        """
        if not self.is_initialized:
            raise ServiceStateError("Chunk storage is not initialized")

        if not chunk:
            raise ValueError("Chunk cannot be None")

        if chunk_id not in self._chunks:
            raise KeyError(f"Chunk with ID {chunk_id} does not exist")

        old_size = len(str(self._chunks[chunk_id]).encode())
        new_size = len(str(chunk).encode())
        size_diff = new_size - old_size

        self._chunks[chunk_id] = chunk
        self._metrics.increment_storage_stat("total_bytes", size_diff)
        self._metrics.increment_operation_count("updates")

    def delete_chunk(self, chunk_id: UUID) -> None:
        """Delete a chunk.

        Args:
            chunk_id: Chunk ID

        Raises:
            ServiceStateError: If storage is not initialized
            KeyError: If chunk does not exist
        """
        if not self.is_initialized:
            raise ServiceStateError("Chunk storage is not initialized")

        if chunk_id not in self._chunks:
            raise KeyError(f"Chunk with ID {chunk_id} does not exist")

        chunk_size = len(str(self._chunks[chunk_id]).encode())
        del self._chunks[chunk_id]
        self._metrics.decrement_storage_stat("chunk_count")
        self._metrics.decrement_storage_stat("total_bytes", chunk_size)
        self._metrics.increment_operation_count("deletes")
