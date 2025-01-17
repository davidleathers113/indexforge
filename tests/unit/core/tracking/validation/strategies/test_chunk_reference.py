"""Tests for the ChunkReferenceValidator."""

import pytest

from src.core.models import ChunkReference, DocumentLineage
from src.core.tracking.validation.strategies.chunks import ChunkReferenceValidator


@pytest.fixture
def validator():
    """Create a ChunkReferenceValidator instance."""
    return ChunkReferenceValidator()


@pytest.fixture
def valid_lineage_data():
    """Create valid lineage data with proper chunk references."""
    return {
        "doc1": DocumentLineage(
            id="doc1",
            chunk_references=[
                ChunkReference(source_doc="doc2", chunk_id="chunk1"),
                ChunkReference(source_doc="doc2", chunk_id="chunk2"),
            ],
        ),
        "doc2": DocumentLineage(
            id="doc2",
            chunks={"chunk1": "content1", "chunk2": "content2"},
        ),
    }


def test_validate_valid_chunk_references(validator, valid_lineage_data):
    """Test validation with valid chunk references."""
    errors = validator.validate(valid_lineage_data)
    assert len(errors) == 0


def test_validate_missing_source_document(validator):
    """Test validation with missing source document."""
    lineage_data = {
        "doc1": DocumentLineage(
            id="doc1",
            chunk_references=[ChunkReference(source_doc="doc2", chunk_id="chunk1")],
        ),
    }
    errors = validator.validate(lineage_data)
    assert len(errors) > 0
    assert any("missing" in error.lower() for error in errors)


def test_validate_missing_chunk(validator):
    """Test validation with missing chunk in source document."""
    lineage_data = {
        "doc1": DocumentLineage(
            id="doc1",
            chunk_references=[ChunkReference(source_doc="doc2", chunk_id="chunk1")],
        ),
        "doc2": DocumentLineage(
            id="doc2",
            chunks={},
        ),
    }
    errors = validator.validate(lineage_data)
    assert len(errors) > 0
    assert any("chunk" in error.lower() for error in errors)


def test_validate_empty_lineage(validator):
    """Test validation with empty lineage data."""
    errors = validator.validate({})
    assert len(errors) == 0


def test_validate_no_chunk_references(validator):
    """Test validation with documents having no chunk references."""
    lineage_data = {
        "doc1": DocumentLineage(id="doc1"),
        "doc2": DocumentLineage(id="doc2"),
    }
    errors = validator.validate(lineage_data)
    assert len(errors) == 0


def test_validate_multiple_invalid_references(validator):
    """Test validation with multiple invalid chunk references."""
    lineage_data = {
        "doc1": DocumentLineage(
            id="doc1",
            chunk_references=[
                ChunkReference(source_doc="doc2", chunk_id="chunk1"),
                ChunkReference(source_doc="doc3", chunk_id="chunk2"),
            ],
        ),
        "doc2": DocumentLineage(
            id="doc2",
            chunks={},
        ),
    }
    errors = validator.validate(lineage_data)
    assert len(errors) >= 2  # Should have at least 2 errors
