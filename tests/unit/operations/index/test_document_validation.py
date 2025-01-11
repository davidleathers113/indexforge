"""Test document validation functionality of IndexOperation."""

from unittest.mock import Mock

import pytest

from src.api.repositories.weaviate.exceptions import DocumentValidationError
from src.api.repositories.weaviate.operations.index import IndexOperation

# Test data constants
VALID_DOCUMENT = {"id": "1", "text": "Sample text", "metadata": {"source": "test"}}


@pytest.fixture
def index_operation():
    """Setup IndexOperation instance with mocked dependencies."""
    vector_service = Mock()
    vector_service.encode.return_value = [[0.1, 0.2, 0.3]]
    return IndexOperation(vector_service=vector_service)


def test_validate_required_fields(index_operation):
    """
    Test validation of required fields.

    Given: Documents with missing required fields
    When: Validating the documents
    Then: Appropriate validation errors should be raised
    """
    missing_text = {"id": "1", "metadata": {"source": "test"}}
    missing_id = {"text": "Sample", "metadata": {"source": "test"}}

    with pytest.raises(DocumentValidationError, match="Missing required field: text"):
        index_operation.validate_document(missing_text)

    with pytest.raises(DocumentValidationError, match="Missing required field: id"):
        index_operation.validate_document(missing_id)

    # Valid document should not raise
    index_operation.validate_document(VALID_DOCUMENT)


def test_validate_field_types(index_operation):
    """
    Test validation of field types.

    Given: Documents with incorrect field types
    When: Validating the documents
    Then: Appropriate validation errors should be raised
    """
    invalid_id_type = {"id": 1, "text": "Sample", "metadata": {"source": "test"}}
    invalid_text_type = {"id": "1", "text": 123, "metadata": {"source": "test"}}
    invalid_metadata_type = {"id": "1", "text": "Sample", "metadata": "not_a_dict"}

    with pytest.raises(DocumentValidationError, match="Invalid type for field 'id'"):
        index_operation.validate_document(invalid_id_type)

    with pytest.raises(DocumentValidationError, match="Invalid type for field 'text'"):
        index_operation.validate_document(invalid_text_type)

    with pytest.raises(DocumentValidationError, match="Invalid type for field 'metadata'"):
        index_operation.validate_document(invalid_metadata_type)


def test_validate_field_constraints(index_operation):
    """
    Test validation of field constraints.

    Given: Documents with fields violating constraints
    When: Validating the documents
    Then: Appropriate validation errors should be raised
    """
    empty_text = {"id": "1", "text": "", "metadata": {"source": "test"}}
    long_id = {"id": "a" * 100, "text": "Sample", "metadata": {"source": "test"}}

    with pytest.raises(DocumentValidationError, match="Text field cannot be empty"):
        index_operation.validate_document(empty_text)

    with pytest.raises(DocumentValidationError, match="ID exceeds maximum length"):
        index_operation.validate_document(long_id)


def test_validate_metadata_structure(index_operation):
    """
    Test validation of metadata structure.

    Given: Documents with invalid metadata structures
    When: Validating the documents
    Then: Appropriate validation errors should be raised
    """
    invalid_source = {"id": "1", "text": "Sample", "metadata": {"source": None}}
    missing_source = {"id": "1", "text": "Sample", "metadata": {}}

    with pytest.raises(DocumentValidationError, match="Invalid source in metadata"):
        index_operation.validate_document(invalid_source)

    with pytest.raises(DocumentValidationError, match="Missing source in metadata"):
        index_operation.validate_document(missing_source)


def test_validate_custom_fields(index_operation):
    """
    Test validation of custom fields.

    Given: Documents with custom fields
    When: Validating the documents
    Then: Custom fields should be validated according to rules
    """
    invalid_custom_field = {
        **VALID_DOCUMENT,
        "custom_field": {"invalid": lambda x: x},  # Non-serializable value
    }

    with pytest.raises(DocumentValidationError, match="Invalid value for custom field"):
        index_operation.validate_document(invalid_custom_field)

    # Valid custom fields should not raise
    valid_custom_fields = {
        **VALID_DOCUMENT,
        "custom_field": "value",
        "number_field": 123,
        "nested": {"valid": "value"},
    }
    index_operation.validate_document(valid_custom_fields)
