"""Memory-based storage implementation.

This module provides a thread-safe in-memory storage implementation
that conforms to the core storage interfaces.
"""

from __future__ import annotations

import logging
import threading
from typing import Dict, Generic, TypeVar
from uuid import UUID

from src.core.interfaces.storage import (
    ChunkStorage,
    DocumentStorage,
    LineageStorage,
    ReferenceStorage,
)
from src.core.models.chunks import Chunk
from src.core.models.documents import Document
from src.core.models.lineage import DocumentLineage
from src.core.models.references import Reference
from src.core.settings import Settings

from .exceptions import MemoryStorageError
from .memory_manager import MemoryManager

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Document)
C = TypeVar("C", bound=Chunk)
R = TypeVar("R", bound=Reference)


class MemoryStorage(
    Generic[T, C, R], DocumentStorage[T], ChunkStorage, ReferenceStorage, LineageStorage
):
    """Thread-safe in-memory storage implementation."""

    def __init__(self, settings: Settings) -> None:
        """Initialize memory storage.

        Args:
            settings: Application settings for configuring storage behavior
        """
        self._settings = settings
        self._lock = threading.RLock()
        self._manager = MemoryManager[T](
            max_size_bytes=settings.storage.max_size_bytes,
            max_items=settings.storage.max_items,
        )

        # Storage containers
        self._documents: Dict[UUID, T] = {}
        self._chunks: Dict[UUID, C] = {}
        self._references: Dict[UUID, list[R]] = {}
        self._lineage: Dict[str, DocumentLineage] = {}

    def store_document(self, document: T) -> UUID:
        """Store a document thread-safely.

        Args:
            document: Document to store

        Returns:
            UUID of stored document

        Raises:
            MemoryStorageError: If storage fails
        """
        try:
            with self._lock:
                # Validate capacity
                self._manager.check_item_limit(len(self._documents) + 1)
                size = self._manager.estimate_size(document.dict())
                self._manager.check_size_limit(size)

                # Store document
                self._documents[document.id] = document
                self._manager.update_usage(document, size)
                return document.id

        except Exception as e:
            logger.exception("Failed to store document %s", document.id)
            raise MemoryStorageError(f"Failed to store document: {e}") from e

    def get_document(self, document_id: UUID) -> T:
        """Retrieve a document thread-safely.

        Args:
            document_id: ID of document to retrieve

        Returns:
            Retrieved document

        Raises:
            KeyError: If document not found
            MemoryStorageError: If retrieval fails
        """
        try:
            with self._lock:
                return self._documents[document_id]
        except KeyError as e:
            raise KeyError(f"Document not found: {document_id}") from e
        except Exception as e:
            logger.exception("Failed to retrieve document %s", document_id)
            raise MemoryStorageError(f"Failed to retrieve document: {e}") from e

    def update_document(self, document_id: UUID, document: T) -> None:
        """Update a document thread-safely.

        Args:
            document_id: ID of document to update
            document: Updated document

        Raises:
            KeyError: If document not found
            MemoryStorageError: If update fails
        """
        try:
            with self._lock:
                if document_id not in self._documents:
                    raise KeyError(f"Document not found: {document_id}")

                # Calculate size difference
                old_size = self._manager.estimate_size(self._documents[document_id].dict())
                new_size = self._manager.estimate_size(document.dict())
                size_delta = new_size - old_size

                # Check if new size is allowed
                if size_delta > 0:
                    self._manager.check_size_limit(size_delta)

                # Update document
                self._documents[document_id] = document
                self._manager.update_usage(document, size_delta)

        except KeyError as e:
            raise e
        except Exception as e:
            logger.exception("Failed to update document %s", document_id)
            raise MemoryStorageError(f"Failed to update document: {e}") from e

    def delete_document(self, document_id: UUID) -> None:
        """Delete a document thread-safely.

        Args:
            document_id: ID of document to delete

        Raises:
            KeyError: If document not found
            MemoryStorageError: If deletion fails
        """
        try:
            with self._lock:
                if document_id not in self._documents:
                    raise KeyError(f"Document not found: {document_id}")

                # Calculate size to remove
                size = self._manager.estimate_size(self._documents[document_id].dict())

                # Delete document
                del self._documents[document_id]
                self._manager.update_usage(document_id, -size)

        except KeyError as e:
            raise e
        except Exception as e:
            logger.exception("Failed to delete document %s", document_id)
            raise MemoryStorageError(f"Failed to delete document: {e}") from e

    def store_chunk(self, chunk: C) -> UUID:
        """Store a chunk thread-safely.

        Args:
            chunk: Chunk to store

        Returns:
            UUID of stored chunk

        Raises:
            MemoryStorageError: If storage fails
        """
        try:
            with self._lock:
                # Validate capacity
                self._manager.check_item_limit(len(self._chunks) + 1)
                size = self._manager.estimate_size(chunk.dict())
                self._manager.check_size_limit(size)

                # Store chunk
                self._chunks[chunk.id] = chunk
                self._manager.update_usage(chunk, size)
                return chunk.id

        except Exception as e:
            logger.exception("Failed to store chunk %s", chunk.id)
            raise MemoryStorageError(f"Failed to store chunk: {e}") from e

    def get_chunk(self, chunk_id: UUID) -> C | None:
        """Get a chunk by ID thread-safely.

        Args:
            chunk_id: ID of chunk to retrieve

        Returns:
            Retrieved chunk or None if not found

        Raises:
            MemoryStorageError: If retrieval fails
        """
        try:
            with self._lock:
                return self._chunks.get(chunk_id)
        except Exception as e:
            logger.exception("Failed to retrieve chunk %s", chunk_id)
            raise MemoryStorageError(f"Failed to retrieve chunk: {e}") from e

    def update_chunk(self, chunk_id: UUID, chunk: C) -> None:
        """Update a chunk thread-safely.

        Args:
            chunk_id: ID of chunk to update
            chunk: Updated chunk

        Raises:
            KeyError: If chunk not found
            MemoryStorageError: If update fails
        """
        try:
            with self._lock:
                if chunk_id not in self._chunks:
                    raise KeyError(f"Chunk not found: {chunk_id}")

                # Calculate size difference
                old_size = self._manager.estimate_size(self._chunks[chunk_id].dict())
                new_size = self._manager.estimate_size(chunk.dict())
                size_delta = new_size - old_size

                # Check if new size is allowed
                if size_delta > 0:
                    self._manager.check_size_limit(size_delta)

                # Update chunk
                self._chunks[chunk_id] = chunk
                self._manager.update_usage(chunk, size_delta)

        except KeyError as e:
            raise e
        except Exception as e:
            logger.exception("Failed to update chunk %s", chunk_id)
            raise MemoryStorageError(f"Failed to update chunk: {e}") from e

    def delete_chunk(self, chunk_id: UUID) -> None:
        """Delete a chunk thread-safely.

        Args:
            chunk_id: ID of chunk to delete

        Raises:
            KeyError: If chunk not found
            MemoryStorageError: If deletion fails
        """
        try:
            with self._lock:
                if chunk_id not in self._chunks:
                    raise KeyError(f"Chunk not found: {chunk_id}")

                # Calculate size to remove
                size = self._manager.estimate_size(self._chunks[chunk_id].dict())

                # Delete chunk
                del self._chunks[chunk_id]
                self._manager.update_usage(chunk_id, -size)

        except KeyError as e:
            raise e
        except Exception as e:
            logger.exception("Failed to delete chunk %s", chunk_id)
            raise MemoryStorageError(f"Failed to delete chunk: {e}") from e

    def store_reference(self, ref: R) -> None:
        """Store a reference thread-safely.

        Args:
            ref: Reference to store

        Raises:
            MemoryStorageError: If storage fails
        """
        try:
            with self._lock:
                # Initialize list if needed
                if ref.chunk_id not in self._references:
                    self._references[ref.chunk_id] = []

                # Check for duplicates
                if ref not in self._references[ref.chunk_id]:
                    size = self._manager.estimate_size(ref.dict())
                    self._manager.check_size_limit(size)

                    # Store reference
                    self._references[ref.chunk_id].append(ref)
                    self._manager.update_usage(ref, size)

        except Exception as e:
            logger.exception("Failed to store reference for chunk %s", ref.chunk_id)
            raise MemoryStorageError(f"Failed to store reference: {e}") from e

    def get_references(self, chunk_id: UUID) -> list[R]:
        """Get references for a chunk thread-safely.

        Args:
            chunk_id: Chunk ID to get references for

        Returns:
            List of references for the chunk

        Raises:
            MemoryStorageError: If retrieval fails
        """
        try:
            with self._lock:
                return self._references.get(chunk_id, [])
        except Exception as e:
            logger.exception("Failed to retrieve references for chunk %s", chunk_id)
            raise MemoryStorageError(f"Failed to retrieve references: {e}") from e

    def delete_reference(self, ref: R) -> None:
        """Delete a reference thread-safely.

        Args:
            ref: Reference to delete

        Raises:
            KeyError: If reference not found
            MemoryStorageError: If deletion fails
        """
        try:
            with self._lock:
                if ref.chunk_id not in self._references:
                    raise KeyError(f"No references found for chunk: {ref.chunk_id}")

                refs = self._references[ref.chunk_id]
                if ref not in refs:
                    raise KeyError(f"Reference not found for chunk: {ref.chunk_id}")

                # Calculate size to remove
                size = self._manager.estimate_size(ref.dict())

                # Remove reference
                refs.remove(ref)
                self._manager.update_usage(ref, -size)

                # Clean up empty list
                if not refs:
                    del self._references[ref.chunk_id]

        except KeyError as e:
            raise e
        except Exception as e:
            logger.exception("Failed to delete reference for chunk %s", ref.chunk_id)
            raise MemoryStorageError(f"Failed to delete reference: {e}") from e

    def get_lineage(self, doc_id: str) -> DocumentLineage | None:
        """Get lineage information for a document thread-safely.

        Args:
            doc_id: Document ID to get lineage for

        Returns:
            Document lineage if found, None otherwise

        Raises:
            MemoryStorageError: If retrieval fails
        """
        try:
            with self._lock:
                return self._lineage.get(doc_id)
        except Exception as e:
            logger.exception("Failed to retrieve lineage for document %s", doc_id)
            raise MemoryStorageError(f"Failed to retrieve lineage: {e}") from e

    def save_lineage(self, lineage: DocumentLineage) -> None:
        """Save lineage information thread-safely.

        Args:
            lineage: Document lineage to save

        Raises:
            MemoryStorageError: If save fails
        """
        try:
            with self._lock:
                size = self._manager.estimate_size(lineage.dict())

                # If updating, remove old size
                if lineage.doc_id in self._lineage:
                    old_size = self._manager.estimate_size(self._lineage[lineage.doc_id].dict())
                    size_delta = size - old_size
                    if size_delta > 0:
                        self._manager.check_size_limit(size_delta)
                    self._manager.update_usage(lineage, size_delta)
                else:
                    # New lineage
                    self._manager.check_size_limit(size)
                    self._manager.update_usage(lineage, size)

                self._lineage[lineage.doc_id] = lineage

        except Exception as e:
            logger.exception("Failed to save lineage for document %s", lineage.doc_id)
            raise MemoryStorageError(f"Failed to save lineage: {e}") from e

    def delete_lineage(self, doc_id: str) -> None:
        """Delete lineage information thread-safely.

        Args:
            doc_id: Document ID to delete lineage for

        Raises:
            KeyError: If lineage not found
            MemoryStorageError: If deletion fails
        """
        try:
            with self._lock:
                if doc_id not in self._lineage:
                    raise KeyError(f"Lineage not found for document: {doc_id}")

                # Calculate size to remove
                size = self._manager.estimate_size(self._lineage[doc_id].dict())

                # Delete lineage
                del self._lineage[doc_id]
                self._manager.update_usage(doc_id, -size)

        except KeyError as e:
            raise e
        except Exception as e:
            logger.exception("Failed to delete lineage for document %s", doc_id)
            raise MemoryStorageError(f"Failed to delete lineage: {e}") from e
