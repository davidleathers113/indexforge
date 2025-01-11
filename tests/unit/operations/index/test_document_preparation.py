"""Test document preparation functionality of IndexOperation."""

from unittest.mock import Mock

import pytest

from src.api.repositories.weaviate.operations.index import IndexOperation

# Test data constants
TEST_DOCUMENTS = [
    {"id": "1", "text": "Sample text", "metadata": {"source": "test"}},
    {"id": "2", "text": "Another text", "metadata": {"source": "test"}},
]


@pytest.fixture
def index_operation():
    """Setup IndexOperation instance with mocked dependencies."""
    vector_service = Mock()
    vector_service.encode.return_value = [[0.1, 0.2, 0.3]]
    return IndexOperation(vector_service=vector_service)


def test_prepare_single_document(index_operation):
    """
    Test preparation of a single document.

    Given: A valid document with required fields
    When: Preparing the document for indexing
    Then: Document should be properly formatted with all required fields
    """
    document = TEST_DOCUMENTS[0]

    prepared = index_operation.prepare_document(document)

    assert "id" in prepared, "Prepared document should contain ID"
    assert "vector" in prepared, "Prepared document should contain vector"
    assert prepared["properties"] == {"text": document["text"], "metadata": document["metadata"]}


def test_prepare_document_with_custom_fields(index_operation):
    """
    Test preparation of document with custom fields.

    Given: A document with additional custom fields
    When: Preparing the document for indexing
    Then: Custom fields should be properly included in properties
    """
    document = {**TEST_DOCUMENTS[0], "custom_field": "value", "another_field": 123}

    prepared = index_operation.prepare_document(document)

    assert prepared["properties"]["custom_field"] == "value"
    assert prepared["properties"]["another_field"] == 123


def test_prepare_document_handles_nested_fields(index_operation):
    """
    Test preparation of document with nested fields.

    Given: A document with nested field structures
    When: Preparing the document for indexing
    Then: Nested fields should be properly flattened or preserved as needed
    """
    document = {
        "id": "1",
        "text": "Sample",
        "nested": {"field1": "value1", "field2": {"subfield": "value2"}},
    }

    prepared = index_operation.prepare_document(document)

    assert "nested" in prepared["properties"]
    assert prepared["properties"]["nested"]["field1"] == "value1"
    assert prepared["properties"]["nested"]["field2"]["subfield"] == "value2"


def test_prepare_document_removes_excluded_fields(index_operation):
    """
    Test excluded fields are removed during preparation.

    Given: A document with fields that should be excluded
    When: Preparing the document for indexing
    Then: Excluded fields should not appear in prepared document
    """
    document = {**TEST_DOCUMENTS[0], "_internal": "value", "__temp": "temporary"}

    prepared = index_operation.prepare_document(document)

    assert "_internal" not in prepared["properties"]
    assert "__temp" not in prepared["properties"]


def test_prepare_document_handles_empty_fields(index_operation):
    """
    Test preparation of document with empty fields.

    Given: A document with empty or null fields
    When: Preparing the document for indexing
    Then: Empty fields should be handled appropriately
    """
    document = {"id": "1", "text": "", "null_field": None, "empty_list": [], "empty_dict": {}}

    prepared = index_operation.prepare_document(document)

    assert prepared["properties"]["text"] == ""
    assert prepared["properties"]["null_field"] is None
    assert prepared["properties"]["empty_list"] == []
    assert prepared["properties"]["empty_dict"] == {}
