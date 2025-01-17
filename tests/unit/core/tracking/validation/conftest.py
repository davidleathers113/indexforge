"""Shared fixtures for validation tests."""

import pytest

from src.core.models import ChunkReference, DocumentLineage


@pytest.fixture
def basic_document():
    """Create a basic document without any relationships or references."""
    return DocumentLineage(id="doc1")


@pytest.fixture
def document_with_chunks():
    """Create a document with chunks."""
    return DocumentLineage(
        id="doc1",
        chunks={
            "chunk1": "content1",
            "chunk2": "content2",
        },
    )


@pytest.fixture
def document_with_references():
    """Create a document with chunk references."""
    return DocumentLineage(
        id="doc1",
        chunk_references=[
            ChunkReference(source_doc="doc2", chunk_id="chunk1"),
            ChunkReference(source_doc="doc2", chunk_id="chunk2"),
        ],
    )


@pytest.fixture
def document_with_relationships():
    """Create a document with relationships."""
    return DocumentLineage(
        id="doc1",
        parents=["parent1", "parent2"],
        children=["child1", "child2"],
        derived_from="parent1",
        derived_documents=["child1"],
    )


@pytest.fixture
def complex_document():
    """Create a document with all types of relationships and references."""
    return DocumentLineage(
        id="doc1",
        parents=["parent1"],
        children=["child1"],
        derived_from="parent1",
        derived_documents=["child1"],
        chunks={"chunk1": "content1"},
        chunk_references=[ChunkReference(source_doc="parent1", chunk_id="source_chunk")],
    )
