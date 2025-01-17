"""Tests for the CircularDependencyValidator."""

import pytest

from src.core.models import DocumentLineage
from src.core.tracking.validation.strategies.circular import CircularDependencyValidator


@pytest.fixture
def validator():
    """Create a CircularDependencyValidator instance."""
    return CircularDependencyValidator()


@pytest.fixture
def simple_lineage_data():
    """Create a simple lineage dataset without circular dependencies."""
    return {
        "doc1": DocumentLineage(id="doc1", derived_documents=["doc2"]),
        "doc2": DocumentLineage(id="doc2", derived_from="doc1"),
    }


@pytest.fixture
def circular_lineage_data():
    """Create a lineage dataset with circular dependencies."""
    return {
        "doc1": DocumentLineage(id="doc1", derived_documents=["doc2"]),
        "doc2": DocumentLineage(id="doc2", derived_documents=["doc3"], derived_from="doc1"),
        "doc3": DocumentLineage(id="doc3", derived_documents=["doc1"], derived_from="doc2"),
    }


def test_validate_no_circular_dependencies(validator, simple_lineage_data):
    """Test validation with no circular dependencies."""
    errors = validator.validate(simple_lineage_data)
    assert len(errors) == 0


def test_validate_with_circular_dependencies(validator, circular_lineage_data):
    """Test validation with circular dependencies."""
    errors = validator.validate(circular_lineage_data)
    assert len(errors) > 0
    assert any("circular" in error.lower() for error in errors)


def test_validate_self_reference(validator):
    """Test validation with self-referential document."""
    lineage_data = {
        "doc1": DocumentLineage(id="doc1", derived_documents=["doc1"]),
    }
    errors = validator.validate(lineage_data)
    assert len(errors) > 0
    assert any("itself" in error.lower() for error in errors)


def test_validate_empty_lineage(validator):
    """Test validation with empty lineage data."""
    errors = validator.validate({})
    assert len(errors) == 0


def test_validate_missing_derived_document(validator):
    """Test validation with missing derived document reference."""
    lineage_data = {
        "doc1": DocumentLineage(id="doc1", derived_documents=["doc2"]),
    }
    errors = validator.validate(lineage_data)
    assert len(errors) > 0
    assert any("missing" in error.lower() for error in errors)


def test_validate_complex_circular_chain(validator):
    """Test validation with a complex chain of circular dependencies."""
    lineage_data = {
        "doc1": DocumentLineage(id="doc1", derived_documents=["doc2"]),
        "doc2": DocumentLineage(id="doc2", derived_documents=["doc3"], derived_from="doc1"),
        "doc3": DocumentLineage(id="doc3", derived_documents=["doc4"], derived_from="doc2"),
        "doc4": DocumentLineage(id="doc4", derived_documents=["doc1"], derived_from="doc3"),
    }
    errors = validator.validate(lineage_data)
    assert len(errors) > 0
    assert any("circular" in error.lower() for error in errors)
