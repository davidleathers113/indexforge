"""Document state for testing."""

from dataclasses import dataclass, field
from datetime import datetime
import logging
import uuid

import pytest

from ..core.base import BaseState


logger = logging.getLogger(__name__)


@dataclass
class DocumentState(BaseState):
    """Document state management."""

    documents: dict[str, dict] = field(default_factory=dict)
    next_id: int = 1
    chunk_size: int = 500
    embedding_dimensions: int = 3
    model_version: str = "1.0.0"
    model_name: str = "test-model"
    error_mode: bool = False

    def reset(self):
        """Reset state to defaults."""
        super().reset()
        self.documents.clear()
        self.next_id = 1
        self.chunk_size = 500
        self.error_mode = False

    def create_uuid(self) -> str:
        """Generate a deterministic UUID for testing."""
        # Create a UUID based on the next_id
        id_bytes = str(self.next_id).zfill(12).encode()
        namespace = uuid.UUID("12345678-1234-5678-1234-567812345678")
        self.next_id += 1
        return str(uuid.uuid5(namespace, id_bytes.hex()))

    def create_embedding(self) -> list[float]:
        """Generate a test embedding vector."""
        return [0.1 * (i + 1) for i in range(self.embedding_dimensions)]

    def create_document(
        self,
        content: str = "Test content",
        title: str = "Test Document",
        summary: str = None,
        parent_id: str = None,
        chunk_ids: list[str] = None,
        with_embeddings: bool = True,
    ) -> dict:
        """Create a test document with optional features."""
        doc_id = self.create_uuid()
        doc = {
            "uuid": doc_id,
            "content": {
                "body": content,
                "summary": summary or f"Summary of {content[:50]}...",
            },
            "embeddings": {
                "body": self.create_embedding() if with_embeddings else None,
                "summary": self.create_embedding() if with_embeddings and summary else None,
                "model": self.model_name,
                "version": self.model_version,
            },
            "metadata": {
                "title": title,
                "timestamp_utc": datetime.now().isoformat(),
            },
            "relationships": {
                "parent_id": parent_id,
                "chunk_ids": chunk_ids or [],
            },
        }
        self.documents[doc_id] = doc
        return doc


@pytest.fixture(scope="function")
def doc_state():
    """Shared document state for testing."""
    state = DocumentState()
    yield state
    state.reset()
