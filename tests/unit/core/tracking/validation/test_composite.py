"""Tests for the CompositeValidator."""

import pytest

from src.core.models import ChunkReference, DocumentLineage
from src.core.tracking.validation.composite import CompositeValidator
from src.core.tracking.validation.strategies.chunks import ChunkReferenceValidator
from src.core.tracking.validation.strategies.circular import CircularDependencyValidator
from src.core.tracking.validation.strategies.relationships import RelationshipValidator


@pytest.fixture
def composite_validator():
    """Create a CompositeValidator with all strategies."""
    return CompositeValidator(
        [
            CircularDependencyValidator(),
            ChunkReferenceValidator(),
            RelationshipValidator(),
        ]
    )


@pytest.fixture
def valid_lineage_data():
    """Create valid lineage data that passes all validations."""
    return {
        "doc1": DocumentLineage(
            id="doc1",
            children=["doc2"],
            derived_documents=["doc2"],
            chunks={"chunk1": "content1"},
        ),
        "doc2": DocumentLineage(
            id="doc2",
            parents=["doc1"],
            derived_from="doc1",
            chunk_references=[ChunkReference(source_doc="doc1", chunk_id="chunk1")],
        ),
    }


def test_validate_valid_data(composite_validator, valid_lineage_data):
    """Test validation with valid data that should pass all strategies."""
    errors = composite_validator.validate(valid_lineage_data)
    assert len(errors) == 0


def test_validate_empty_data(composite_validator):
    """Test validation with empty data."""
    errors = composite_validator.validate({})
    assert len(errors) == 0


def test_validate_multiple_errors(composite_validator):
    """Test validation with data that triggers multiple validation errors."""
    lineage_data = {
        "doc1": DocumentLineage(
            id="doc1",
            derived_documents=["doc2"],
            chunk_references=[ChunkReference(source_doc="missing_doc", chunk_id="chunk1")],
        ),
        "doc2": DocumentLineage(
            id="doc2",
            derived_documents=["doc1"],  # Creates circular dependency
        ),
    }
    errors = composite_validator.validate(lineage_data)
    assert len(errors) >= 2  # Should have multiple errors

    # Check for specific error types
    error_types = [error.lower() for error in errors]
    assert any("circular" in error for error in error_types)
    assert any("missing" in error for error in error_types)


def test_create_default_validator():
    """Test creation of default validator with standard strategies."""
    validator = CompositeValidator.create_default()
    assert len(validator.strategies) >= 3  # Should have at least 3 default strategies


def test_validate_with_subset_of_strategies():
    """Test validation using only a subset of strategies."""
    validator = CompositeValidator(
        [
            CircularDependencyValidator(),
            ChunkReferenceValidator(),
        ]
    )

    # Data with relationship error but no circular or chunk reference issues
    lineage_data = {
        "doc1": DocumentLineage(
            id="doc1",
            children=["doc2"],
        ),
        "doc2": DocumentLineage(
            id="doc2",
            # Missing parent reference, but this strategy isn't included
        ),
    }

    errors = validator.validate(lineage_data)
    assert len(errors) == 0  # Should pass as relationship validation is not included


def test_validate_error_aggregation(composite_validator):
    """Test that errors from all strategies are properly aggregated."""
    lineage_data = {
        "doc1": DocumentLineage(
            id="doc1",
            derived_documents=["doc2"],
            chunk_references=[ChunkReference(source_doc="doc3", chunk_id="chunk1")],
        ),
        "doc2": DocumentLineage(
            id="doc2",
            derived_documents=["doc1"],  # Circular dependency
            parents=["missing_parent"],  # Missing parent reference
        ),
    }

    errors = composite_validator.validate(lineage_data)
    error_text = " ".join(errors).lower()

    # Check for presence of different error types
    assert "circular" in error_text
    assert "missing" in error_text
    assert len(errors) >= 3  # Should have multiple types of errors
