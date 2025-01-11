"""Test document preparation functionality of DeleteOperation."""

from unittest.mock import Mock

import pytest

from src.api.repositories.weaviate.exceptions import DocumentPreparationError
from src.api.repositories.weaviate.operations.delete import DeleteOperation

# Test data constants
TEST_DOCUMENTS = [
    {"id": "550e8400-e29b-41d4-a716-446655440000"},
    {"id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8"},
]


@pytest.fixture
def delete_operation():
    """Setup DeleteOperation instance with mocked dependencies."""
    collection = Mock()
    collection.batch.delete_objects.return_value = {"status": "SUCCESS"}
    return DeleteOperation(collection=collection)


def test_prepare_single_document(delete_operation):
    """
    Test preparation of a single document for deletion.

    Given: A document with a valid UUID
    When: Preparing the document for deletion
    Then: Document should be properly formatted with required fields
    """
    document = TEST_DOCUMENTS[0]

    prepared = delete_operation.prepare_document(document)

    assert "id" in prepared
    assert prepared["id"] == document["id"]
    assert "properties" not in prepared


def test_prepare_document_strips_extra_fields(delete_operation):
    """
    Test preparation removes unnecessary fields.

    Given: A document with extra fields
    When: Preparing the document for deletion
    Then: Only the ID should be retained
    """
    document = {"id": TEST_DOCUMENTS[0]["id"], "extra": "field", "metadata": {"source": "test"}}

    prepared = delete_operation.prepare_document(document)

    assert "id" in prepared
    assert "extra" not in prepared
    assert "metadata" not in prepared
    assert len(prepared.keys()) == 1


def test_prepare_document_validates_uuid(delete_operation):
    """
    Test UUID validation during preparation.

    Given: A document with an invalid UUID
    When: Preparing the document for deletion
    Then: Appropriate error should be raised
    """
    document = {"id": "not-a-uuid"}

    with pytest.raises(DocumentPreparationError, match="Invalid UUID format"):
        delete_operation.prepare_document(document)


def test_prepare_document_requires_id(delete_operation):
    """
    Test ID requirement validation.

    Given: A document without an ID
    When: Preparing the document for deletion
    Then: Appropriate error should be raised
    """
    document = {"other_field": "value"}

    with pytest.raises(DocumentPreparationError, match="Document must contain 'id' field"):
        delete_operation.prepare_document(document)


def test_prepare_document_handles_none_values(delete_operation):
    """
    Test handling of None values.

    Given: A document with None values
    When: Preparing the document for deletion
    Then: Appropriate error should be raised
    """
    document = {"id": None}

    with pytest.raises(DocumentPreparationError, match="Document ID cannot be None"):
        delete_operation.prepare_document(document)
