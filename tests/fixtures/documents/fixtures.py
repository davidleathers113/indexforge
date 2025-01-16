"""Document fixtures for testing."""

import logging

import pytest

from .state import DocumentState


logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def sample_data(doc_state: DocumentState):
    """Provide test data with state management."""
    data = {
        "basic_document": doc_state.create_document(
            content="Test content",
            title="Test Document",
            with_embeddings=False,
        ),
        "document_with_relationships": doc_state.create_document(
            content="Parent document",
            title="Parent Doc",
            chunk_ids=["chunk-1", "chunk-2"],
            with_embeddings=True,
        ),
    }
    return data


@pytest.fixture(scope="function")
def sample_document(doc_state: DocumentState):
    """Sample document for testing with state management."""
    return doc_state.create_document(
        content="This is a test document.",
        title="Test Document",
        with_embeddings=True,
    )


@pytest.fixture(scope="function")
def sample_documents(doc_state: DocumentState):
    """Returns a list of sample documents with state management."""
    return [
        doc_state.create_document(
            content=f"Test document {i}",
            title=f"Test Document {i}",
            with_embeddings=True,
        )
        for i in range(3)
    ]


@pytest.fixture(scope="function")
def document_with_relationships(doc_state: DocumentState):
    """Sample document with relationship data and state management."""
    parent = doc_state.create_document(
        content="Parent document content",
        title="Parent Document",
        with_embeddings=True,
    )
    chunks = [
        doc_state.create_document(
            content=f"Chunk {i} content",
            title=f"Chunk {i}",
            parent_id=parent["uuid"],
            with_embeddings=True,
        )
        for i in range(2)
    ]
    parent["relationships"]["chunk_ids"] = [chunk["uuid"] for chunk in chunks]
    return parent


@pytest.fixture(scope="function")
def large_document(doc_state: DocumentState):
    """Large document that triggers chunking with state management."""
    content = " ".join([f"word{i}" for i in range(2000)])
    return doc_state.create_document(
        content=content,
        title="Large Document",
        with_embeddings=False,
    )
