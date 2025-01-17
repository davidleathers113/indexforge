"""Tests for the RelationshipValidator."""

import pytest

from src.core.models import DocumentLineage
from src.core.tracking.validation.strategies.relationships import RelationshipValidator


@pytest.fixture
def validator():
    """Create a RelationshipValidator instance."""
    return RelationshipValidator()


@pytest.fixture
def valid_lineage_data():
    """Create valid lineage data with proper relationships."""
    return {
        "parent": DocumentLineage(
            id="parent",
            children=["child1", "child2"],
            derived_documents=["child1", "child2"],
        ),
        "child1": DocumentLineage(
            id="child1",
            parents=["parent"],
            derived_from="parent",
        ),
        "child2": DocumentLineage(
            id="child2",
            parents=["parent"],
            derived_from="parent",
        ),
    }


def test_validate_valid_relationships(validator, valid_lineage_data):
    """Test validation with valid relationships."""
    errors = validator.validate(valid_lineage_data)
    assert len(errors) == 0


def test_validate_missing_parent_reference(validator):
    """Test validation with missing parent reference."""
    lineage_data = {
        "child": DocumentLineage(
            id="child",
            parents=["parent"],
            derived_from="parent",
        ),
    }
    errors = validator.validate(lineage_data)
    assert len(errors) > 0
    assert any("missing" in error.lower() for error in errors)


def test_validate_inconsistent_parent_child(validator):
    """Test validation with inconsistent parent-child relationship."""
    lineage_data = {
        "parent": DocumentLineage(
            id="parent",
            children=["child"],
        ),
        "child": DocumentLineage(
            id="child",
            # Missing parent reference
        ),
    }
    errors = validator.validate(lineage_data)
    assert len(errors) > 0
    assert any("inconsistent" in error.lower() for error in errors)


def test_validate_self_derivation(validator):
    """Test validation with self-derivation."""
    lineage_data = {
        "doc": DocumentLineage(
            id="doc",
            derived_from="doc",
        ),
    }
    errors = validator.validate(lineage_data)
    assert len(errors) > 0
    assert any("itself" in error.lower() for error in errors)


def test_validate_inconsistent_derivation(validator):
    """Test validation with inconsistent derivation relationship."""
    lineage_data = {
        "parent": DocumentLineage(
            id="parent",
            derived_documents=["child"],
        ),
        "child": DocumentLineage(
            id="child",
            derived_from="other_doc",  # Inconsistent with parent's derived_documents
        ),
    }
    errors = validator.validate(lineage_data)
    assert len(errors) > 0
    assert any("inconsistent" in error.lower() for error in errors)


def test_validate_empty_lineage(validator):
    """Test validation with empty lineage data."""
    errors = validator.validate({})
    assert len(errors) == 0


def test_validate_multiple_relationship_errors(validator):
    """Test validation with multiple relationship errors."""
    lineage_data = {
        "doc1": DocumentLineage(
            id="doc1",
            children=["doc2"],
            derived_documents=["doc3"],
        ),
        "doc2": DocumentLineage(
            id="doc2",
            # Missing parent reference to doc1
            derived_from="doc3",  # Inconsistent derivation
        ),
    }
    errors = validator.validate(lineage_data)
    assert len(errors) >= 2  # Should have multiple errors
