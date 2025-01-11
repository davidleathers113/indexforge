"""Test UUID generation functionality of IndexOperation."""

import uuid
from unittest.mock import Mock

import pytest

from src.api.repositories.weaviate.exceptions import UUIDGenerationError
from src.api.repositories.weaviate.operations.index import IndexOperation

# Test data constants
TEST_DOCUMENT = {"text": "Sample text", "metadata": {"source": "test"}}


@pytest.fixture
def index_operation():
    """Setup IndexOperation instance with mocked dependencies."""
    vector_service = Mock()
    vector_service.encode.return_value = [[0.1, 0.2, 0.3]]
    return IndexOperation(vector_service=vector_service)


def test_generate_uuid_for_document(index_operation):
    """
    Test UUID generation for document without ID.

    Given: A document without an ID field
    When: Preparing the document
    Then: A valid UUID should be generated and added
    """
    prepared = index_operation.prepare_document(TEST_DOCUMENT)

    assert "id" in prepared
    # Verify it's a valid UUID
    generated_uuid = uuid.UUID(prepared["id"])
    assert isinstance(generated_uuid, uuid.UUID)


def test_uuid_consistency(index_operation):
    """
    Test consistency of UUID generation.

    Given: Multiple preparations of the same document
    When: Preparing the document multiple times
    Then: Different UUIDs should be generated each time
    """
    prepared1 = index_operation.prepare_document(TEST_DOCUMENT)
    prepared2 = index_operation.prepare_document(TEST_DOCUMENT)

    assert prepared1["id"] != prepared2["id"]
    # Verify both are valid UUIDs
    uuid.UUID(prepared1["id"])
    uuid.UUID(prepared2["id"])


def test_preserve_existing_uuid(index_operation):
    """
    Test preservation of existing UUID.

    Given: A document with an existing valid UUID
    When: Preparing the document
    Then: The existing UUID should be preserved
    """
    existing_uuid = str(uuid.uuid4())
    document = {**TEST_DOCUMENT, "id": existing_uuid}

    prepared = index_operation.prepare_document(document)

    assert prepared["id"] == existing_uuid


def test_validate_existing_uuid(index_operation):
    """
    Test validation of existing UUID.

    Given: A document with an invalid UUID
    When: Preparing the document
    Then: Appropriate error should be raised
    """
    document = {**TEST_DOCUMENT, "id": "not-a-uuid"}

    with pytest.raises(UUIDGenerationError, match="Invalid UUID format"):
        index_operation.prepare_document(document)


def test_uuid_version_format(index_operation):
    """
    Test UUID version and format.

    Given: A document requiring UUID generation
    When: Preparing the document
    Then: Generated UUID should be version 4 and properly formatted
    """
    prepared = index_operation.prepare_document(TEST_DOCUMENT)

    generated_uuid = uuid.UUID(prepared["id"])
    assert generated_uuid.version == 4, "UUID should be version 4"
    assert len(prepared["id"]) == 36, "UUID should be properly formatted"
