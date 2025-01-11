"""Test document validation functionality of DeleteOperation."""

from unittest.mock import Mock

import pytest

from src.api.repositories.weaviate.exceptions import DocumentValidationError
from src.api.repositories.weaviate.operations.delete import DeleteOperation

# Test data constants
VALID_DOCUMENT = {"id": "550e8400-e29b-41d4-a716-446655440000"}


@pytest.fixture
def delete_operation():
    """Setup DeleteOperation instance with mocked dependencies."""
    collection = Mock()
    collection.batch.delete_objects.return_value = {"status": "SUCCESS"}
    return DeleteOperation(collection=collection)


def test_validate_document_structure(delete_operation):
    """
    Test validation of document structure.

    Given: Documents with various structural issues
    When: Validating the documents
    Then: Appropriate validation errors should be raised
    """
    empty_doc = {}
    none_doc = None
    array_doc = []

    with pytest.raises(DocumentValidationError, match="Document cannot be empty"):
        delete_operation.validate_document(empty_doc)

    with pytest.raises(DocumentValidationError, match="Document cannot be None"):
        delete_operation.validate_document(none_doc)

    with pytest.raises(DocumentValidationError, match="Document must be a dictionary"):
        delete_operation.validate_document(array_doc)


def test_validate_id_presence(delete_operation):
    """
    Test validation of ID field presence.

    Given: Documents with missing or invalid ID fields
    When: Validating the documents
    Then: Appropriate validation errors should be raised
    """
    missing_id = {"other": "field"}
    empty_id = {"id": ""}
    whitespace_id = {"id": "   "}

    with pytest.raises(DocumentValidationError, match="Document must contain 'id' field"):
        delete_operation.validate_document(missing_id)

    with pytest.raises(DocumentValidationError, match="Document ID cannot be empty"):
        delete_operation.validate_document(empty_id)

    with pytest.raises(DocumentValidationError, match="Document ID cannot be whitespace"):
        delete_operation.validate_document(whitespace_id)


def test_validate_id_format(delete_operation):
    """
    Test validation of ID format.

    Given: Documents with IDs in various formats
    When: Validating the documents
    Then: Appropriate validation errors should be raised
    """
    invalid_format = {"id": "not-a-uuid"}
    malformed_uuid = {"id": "550e8400-e29b-41d4-a716"}

    with pytest.raises(DocumentValidationError, match="Invalid UUID format"):
        delete_operation.validate_document(invalid_format)

    with pytest.raises(DocumentValidationError, match="Malformed UUID"):
        delete_operation.validate_document(malformed_uuid)


def test_validate_id_version(delete_operation):
    """
    Test validation of UUID version.

    Given: Documents with UUIDs of different versions
    When: Validating the documents
    Then: Appropriate validation errors should be raised
    """
    # UUID v1 (time-based)
    uuid_v1 = {"id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8"}
    # UUID v4 (random)
    uuid_v4 = {"id": "550e8400-e29b-41d4-a716-446655440000"}

    # Both v1 and v4 should be valid
    delete_operation.validate_document(uuid_v1)
    delete_operation.validate_document(uuid_v4)


def test_validate_extra_fields(delete_operation):
    """
    Test validation with extra fields.

    Given: Documents with additional fields
    When: Validating the documents
    Then: Validation should pass but log warnings
    """
    extra_fields = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "extra": "field",
        "metadata": {"source": "test"},
    }

    # Should pass validation but log warning
    delete_operation.validate_document(extra_fields)
