"""Tests for the chunk reference validation strategy.

This module contains tests for the ChunkReferenceValidator class, which validates
chunk references within document lineage data.
"""


import pytest

from src.core.models import ChunkReference, DocumentChunk, DocumentLineage
from src.core.tracking.validation.strategies.chunks import ChunkReferenceValidator


@pytest.fixture
def validator() -> ChunkReferenceValidator:
    """Create a ChunkReferenceValidator instance for testing."""
    return ChunkReferenceValidator()


@pytest.fixture
def source_document() -> DocumentLineage:
    """Create a source document with chunks for testing."""
    return DocumentLineage(
        document_id="source-doc-1",
        chunks=[
            DocumentChunk(chunk_id="chunk-1", content="Test content 1"),
            DocumentChunk(chunk_id="chunk-2", content="Test content 2"),
        ],
    )


@pytest.fixture
def derived_document(source_document: DocumentLineage) -> DocumentLineage:
    """Create a derived document with chunk references for testing."""
    return DocumentLineage(
        document_id="derived-doc-1",
        chunk_references=[
            ChunkReference(source_doc_id="source-doc-1", chunk_id="chunk-1"),
            ChunkReference(source_doc_id="source-doc-1", chunk_id="chunk-2"),
        ],
        derived_documents=[source_document],
    )


def test_validate_valid_references(
    validator: ChunkReferenceValidator, derived_document: DocumentLineage
):
    """Test validation with valid chunk references.

    Should return an empty list when all chunk references are valid.
    """
    errors = validator.validate(derived_document)
    assert not errors, "Expected no validation errors for valid chunk references"


def test_validate_duplicate_references(
    validator: ChunkReferenceValidator, source_document: DocumentLineage
):
    """Test validation with duplicate chunk references.

    Should detect and report duplicate chunk references.
    """
    document = DocumentLineage(
        document_id="test-doc",
        chunk_references=[
            ChunkReference(source_doc_id="source-doc-1", chunk_id="chunk-1"),
            ChunkReference(source_doc_id="source-doc-1", chunk_id="chunk-1"),  # Duplicate
        ],
        derived_documents=[source_document],
    )

    errors = validator.validate(document)
    assert len(errors) == 1
    assert "Duplicate chunk reference found: source-doc-1:chunk-1" in errors[0]


def test_validate_missing_source_document(validator: ChunkReferenceValidator):
    """Test validation with references to non-existent source documents.

    Should detect and report missing source documents.
    """
    document = DocumentLineage(
        document_id="test-doc",
        chunk_references=[
            ChunkReference(source_doc_id="non-existent-doc", chunk_id="chunk-1"),
        ],
    )

    errors = validator.validate(document)
    assert len(errors) == 1
    assert "Referenced source document not found: non-existent-doc" in errors[0]


def test_validate_missing_chunk(
    validator: ChunkReferenceValidator, source_document: DocumentLineage
):
    """Test validation with references to non-existent chunks.

    Should detect and report missing chunks in source documents.
    """
    document = DocumentLineage(
        document_id="test-doc",
        chunk_references=[
            ChunkReference(source_doc_id="source-doc-1", chunk_id="non-existent-chunk"),
        ],
        derived_documents=[source_document],
    )

    errors = validator.validate(document)
    assert len(errors) == 1
    assert (
        "Referenced chunk non-existent-chunk not found in source document source-doc-1" in errors[0]
    )


def test_validate_empty_lineage(validator: ChunkReferenceValidator):
    """Test validation with empty lineage data.

    Should handle empty lineage data gracefully.
    """
    errors = validator.validate(None)
    assert not errors, "Expected no validation errors for empty lineage"


def test_validate_no_chunk_references(
    validator: ChunkReferenceValidator, source_document: DocumentLineage
):
    """Test validation with no chunk references.

    Should handle documents without chunk references gracefully.
    """
    document = DocumentLineage(document_id="test-doc", derived_documents=[source_document])

    errors = validator.validate(document)
    assert not errors, "Expected no validation errors for document without chunk references"


def test_validate_multiple_errors(
    validator: ChunkReferenceValidator, source_document: DocumentLineage
):
    """Test validation with multiple validation errors.

    Should detect and report all validation errors in a single pass.
    """
    document = DocumentLineage(
        document_id="test-doc",
        chunk_references=[
            ChunkReference(source_doc_id="source-doc-1", chunk_id="non-existent-chunk"),
            ChunkReference(source_doc_id="non-existent-doc", chunk_id="chunk-1"),
            ChunkReference(
                source_doc_id="source-doc-1", chunk_id="non-existent-chunk"
            ),  # Duplicate
        ],
        derived_documents=[source_document],
    )

    errors = validator.validate(document)
    assert len(errors) == 3, "Expected three validation errors"
    assert any("non-existent-chunk" in error for error in errors)
    assert any("non-existent-doc" in error for error in errors)
    assert any("Duplicate chunk reference" in error for error in errors)


def test_get_source_document_direct(validator: ChunkReferenceValidator):
    """Test retrieving source document when it's the direct document.

    Should find source document when it matches the direct document ID.
    """
    document = DocumentLineage(document_id="test-doc")
    result = validator._get_source_document(document, "test-doc")
    assert result == document


def test_get_source_document_derived(
    validator: ChunkReferenceValidator, derived_document: DocumentLineage
):
    """Test retrieving source document from derived documents.

    Should find source document when it's in the derived documents list.
    """
    result = validator._get_source_document(derived_document, "source-doc-1")
    assert result is not None
    assert result.document_id == "source-doc-1"


def test_chunk_exists_in_document(
    validator: ChunkReferenceValidator, source_document: DocumentLineage
):
    """Test checking chunk existence in a document.

    Should correctly identify existing and non-existing chunks.
    """
    assert validator._chunk_exists_in_document(source_document, "chunk-1")
    assert validator._chunk_exists_in_document(source_document, "chunk-2")
    assert not validator._chunk_exists_in_document(source_document, "non-existent-chunk")
