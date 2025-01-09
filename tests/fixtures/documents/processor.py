"""Document processor for testing."""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from unittest.mock import MagicMock

import pytest

from .state import DocumentState

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def mock_doc_processor(doc_state: DocumentState):
    """Mock document processor for testing."""
    mock_processor = MagicMock()

    def process_document(doc: Dict) -> Dict:
        """Process a document with error tracking."""
        try:
            # Basic validation
            if not doc.get("content"):
                doc_state.add_error("Missing content in document")
                raise ValueError("Missing content in document")

            content = doc["content"].get("body", "")
            if not content:
                doc_state.add_error("Empty document content")
                raise ValueError("Empty document content")

            # Process the document
            chunks = [
                content[i : i + doc_state.chunk_size]
                for i in range(0, len(content), doc_state.chunk_size)
            ]
            return {
                "id": doc.get("id", "test-id"),
                "content": {
                    "body": content,
                    "chunks": chunks,
                    "summary": doc["content"].get("summary", ""),
                },
                "metadata": {
                    "title": doc.get("metadata", {}).get("title", "Untitled"),
                    "timestamp_utc": doc_state.create_document()["metadata"]["timestamp_utc"],
                    "word_count": len(content.split()),
                    "chunk_count": len(chunks),
                },
                "processed": True,
                "pipeline_version": "1.0.0",
            }

        except Exception as e:
            doc_state.add_error(str(e))
            raise

    def set_chunk_size(size: int):
        """Configure chunking size."""
        if size <= 0:
            raise ValueError("Chunk size must be positive")
        doc_state.chunk_size = size

    def batch_documents(documents: List[Dict], batch_size: int) -> List[List[Dict]]:
        """Split documents into batches."""
        try:
            if not documents:
                return []
            return [documents]  # For testing, return single batch
        except Exception as e:
            doc_state.add_error(str(e))
            raise

    def deduplicate_documents(documents: List[Dict]) -> List[Dict]:
        """Mock document deduplication."""
        try:
            # For testing, just process each document
            return [process_document(doc) for doc in documents]
        except Exception as e:
            doc_state.add_error(str(e))
            raise

    # Configure mock methods
    mock_processor.process = MagicMock(side_effect=process_document)
    mock_processor.batch_documents = MagicMock(side_effect=batch_documents)
    mock_processor.deduplicate_documents = MagicMock(side_effect=deduplicate_documents)
    mock_processor.set_chunk_size = MagicMock(side_effect=set_chunk_size)
    mock_processor.get_errors = doc_state.get_errors
    mock_processor.reset = doc_state.reset
    mock_processor.set_error_mode = lambda enabled=True: setattr(doc_state, "error_mode", enabled)

    yield mock_processor
    doc_state.reset()
