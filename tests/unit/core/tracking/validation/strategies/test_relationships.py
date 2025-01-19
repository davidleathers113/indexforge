"""Tests for the relationship validation strategy.

This module contains tests for the RelationshipValidator class, which validates
relationships between documents in lineage data.
"""


import pytest

from src.core.models import DocumentLineage, DocumentReference
from src.core.tracking.validation.strategies.relationships import RelationshipValidator


@pytest.fixture
def validator() -> RelationshipValidator:
    """Create a RelationshipValidator instance for testing."""
    return RelationshipValidator()


@pytest.fixture
def parent_document() -> DocumentLineage:
    """Create a parent document for testing."""
    return DocumentLineage(
        document_id="parent-doc",
        child_documents=[DocumentLineage(document_id="child-doc", parent_id="parent-doc")],
    )


@pytest.fixture
def child_document(parent_document: DocumentLineage) -> DocumentLineage:
    """Create a child document with proper parent reference."""
    return DocumentLineage(document_id="child-doc", parent_id="parent-doc")


@pytest.fixture
def source_document() -> DocumentLineage:
    """Create a source document for testing derivation relationships."""
    return DocumentLineage(
        document_id="source-doc",
        derived_documents=[
            DocumentLineage(
                document_id="derived-doc",
                source_references=[DocumentReference(document_id="source-doc")],
            )
        ],
    )


@pytest.fixture
def derived_document(source_document: DocumentLineage) -> DocumentLineage:
    """Create a derived document with proper source references."""
    return DocumentLineage(
        document_id="derived-doc", source_references=[DocumentReference(document_id="source-doc")]
    )


def test_validate_valid_relationships(
    validator: RelationshipValidator,
    parent_document: DocumentLineage,
    source_document: DocumentLineage,
):
    """Test validation with valid relationships.

    Should return an empty list when all relationships are valid.
    """
    errors = validator.validate(parent_document)
    assert not errors, "Expected no validation errors for valid parent-child relationships"

    errors = validator.validate(source_document)
    assert not errors, "Expected no validation errors for valid derivation relationships"


def test_validate_missing_parent(validator: RelationshipValidator):
    """Test validation with missing parent document reference.

    Should detect and report missing parent document.
    """
    document = DocumentLineage(document_id="test-doc", parent_id="non-existent-parent")

    errors = validator.validate(document)
    assert len(errors) == 1
    assert "Referenced parent document not found: non-existent-parent" in errors[0]


def test_validate_self_parent(validator: RelationshipValidator):
    """Test validation with self-referential parent relationship.

    Should detect and report self-parent reference.
    """
    document = DocumentLineage(document_id="test-doc", parent_id="test-doc")

    errors = validator.validate(document)
    assert len(errors) == 1
    assert "Document cannot be its own parent: test-doc" in errors[0]


def test_validate_inconsistent_parent_child(
    validator: RelationshipValidator, parent_document: DocumentLineage
):
    """Test validation with inconsistent parent-child relationship.

    Should detect and report when parent doesn't reference child or vice versa.
    """
    # Create child without parent reference
    child = DocumentLineage(document_id="child-doc")
    parent = DocumentLineage(document_id="parent-doc", child_documents=[child])

    errors = validator.validate(parent)
    assert len(errors) == 1
    assert "Child document child-doc does not reference this document as parent" in errors[0]


def test_validate_self_child(validator: RelationshipValidator):
    """Test validation with self-referential child relationship.

    Should detect and report self-child reference.
    """
    document = DocumentLineage(
        document_id="test-doc", child_documents=[DocumentLineage(document_id="test-doc")]
    )

    errors = validator.validate(document)
    assert len(errors) == 1
    assert "Document cannot be its own child: test-doc" in errors[0]


def test_validate_self_derivation(validator: RelationshipValidator):
    """Test validation with self-referential derivation.

    Should detect and report self-derivation.
    """
    document = DocumentLineage(
        document_id="test-doc", derived_documents=[DocumentLineage(document_id="test-doc")]
    )

    errors = validator.validate(document)
    assert len(errors) == 1
    assert "Document cannot be derived from itself: test-doc" in errors[0]


def test_validate_duplicate_derivation(validator: RelationshipValidator):
    """Test validation with duplicate derived document references.

    Should detect and report duplicate derivations.
    """
    derived = DocumentLineage(
        document_id="derived-doc", source_references=[DocumentReference(document_id="source-doc")]
    )
    document = DocumentLineage(
        document_id="source-doc", derived_documents=[derived, derived]  # Duplicate reference
    )

    errors = validator.validate(document)
    assert len(errors) == 1
    assert "Duplicate derived document reference: derived-doc" in errors[0]


def test_validate_missing_derived_reference(
    validator: RelationshipValidator, source_document: DocumentLineage
):
    """Test validation with missing source reference in derived document.

    Should detect and report when derived document doesn't reference source.
    """
    derived = DocumentLineage(document_id="derived-doc")  # No source reference
    document = DocumentLineage(document_id="source-doc", derived_documents=[derived])

    errors = validator.validate(document)
    assert len(errors) == 1
    assert "Derived document derived-doc does not reference this document as source" in errors[0]


def test_validate_missing_source_reference(validator: RelationshipValidator):
    """Test validation with missing source document reference.

    Should detect and report missing source document.
    """
    document = DocumentLineage(
        document_id="test-doc",
        source_references=[DocumentReference(document_id="non-existent-source")],
    )

    errors = validator.validate(document)
    assert len(errors) == 1
    assert "Referenced source document not found: non-existent-source" in errors[0]


def test_validate_empty_lineage(validator: RelationshipValidator):
    """Test validation with empty lineage data.

    Should handle empty lineage data gracefully.
    """
    errors = validator.validate(None)
    assert not errors, "Expected no validation errors for empty lineage"


def test_validate_multiple_errors(validator: RelationshipValidator):
    """Test validation with multiple relationship errors.

    Should detect and report all validation errors in a single pass.
    """
    document = DocumentLineage(
        document_id="test-doc",
        parent_id="test-doc",  # Self-parent
        child_documents=[
            DocumentLineage(document_id="test-doc"),  # Self-child
            DocumentLineage(document_id="child-doc"),  # Missing parent reference
        ],
        derived_documents=[DocumentLineage(document_id="test-doc")],  # Self-derivation
    )

    errors = validator.validate(document)
    assert len(errors) == 4, "Expected four validation errors"
    assert any("own parent" in error for error in errors)
    assert any("own child" in error for error in errors)
    assert any("does not reference this document as parent" in error for error in errors)
    assert any("derived from itself" in error for error in errors)


def test_find_document_by_id_direct(validator: RelationshipValidator):
    """Test finding document by ID when it's the direct document.

    Should return the document when ID matches direct document.
    """
    document = DocumentLineage(document_id="test-doc")
    result = validator._find_document_by_id(document, "test-doc")
    assert result == document


def test_find_document_by_id_derived(
    validator: RelationshipValidator, source_document: DocumentLineage
):
    """Test finding document by ID in derived documents.

    Should return the document when found in derived documents.
    """
    result = validator._find_document_by_id(source_document, "derived-doc")
    assert result is not None
    assert result.document_id == "derived-doc"


def test_find_document_by_id_child(
    validator: RelationshipValidator, parent_document: DocumentLineage
):
    """Test finding document by ID in child documents.

    Should return the document when found in child documents.
    """
    result = validator._find_document_by_id(parent_document, "child-doc")
    assert result is not None
    assert result.document_id == "child-doc"


def test_find_document_by_id_not_found(validator: RelationshipValidator):
    """Test finding document by ID when document doesn't exist.

    Should return None when document is not found.
    """
    document = DocumentLineage(document_id="test-doc")
    result = validator._find_document_by_id(document, "non-existent-doc")
    assert result is None
