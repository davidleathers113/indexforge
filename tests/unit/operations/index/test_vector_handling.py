"""Test vector handling functionality of IndexOperation."""

from unittest.mock import Mock

import numpy as np
import pytest

from src.api.repositories.weaviate.exceptions import VectorEncodingError
from src.api.repositories.weaviate.operations.index import IndexOperation

# Test data constants
TEST_DOCUMENT = {
    "id": "1",
    "text": "Sample text for vector encoding",
    "metadata": {"source": "test"},
}


@pytest.fixture
def mock_vector_service():
    """Setup mock vector service."""
    service = Mock()
    service.encode.return_value = np.array([[0.1, 0.2, 0.3]])
    return service


@pytest.fixture
def index_operation(mock_vector_service):
    """Setup IndexOperation instance with mocked vector service."""
    return IndexOperation(vector_service=mock_vector_service)


def test_encode_text_to_vector(index_operation, mock_vector_service):
    """
    Test text to vector encoding.

    Given: A document with text content
    When: Encoding the text to a vector
    Then: Vector service should be called correctly and vector should be added
    """
    document = TEST_DOCUMENT

    prepared = index_operation.prepare_document(document)

    mock_vector_service.encode.assert_called_once_with(document["text"])
    assert "vector" in prepared
    assert len(prepared["vector"]) == 3
    assert all(isinstance(x, float) for x in prepared["vector"])


def test_handle_encoding_error(index_operation, mock_vector_service):
    """
    Test handling of vector encoding errors.

    Given: A document where vector encoding fails
    When: Preparing the document
    Then: Appropriate error should be raised
    """
    mock_vector_service.encode.side_effect = Exception("Encoding failed")

    with pytest.raises(VectorEncodingError, match="Failed to encode text to vector"):
        index_operation.prepare_document(TEST_DOCUMENT)


def test_handle_empty_vector(index_operation, mock_vector_service):
    """
    Test handling of empty vector result.

    Given: Vector service returns empty vector
    When: Preparing the document
    Then: Appropriate error should be raised
    """
    mock_vector_service.encode.return_value = np.array([[]])

    with pytest.raises(VectorEncodingError, match="Empty vector generated"):
        index_operation.prepare_document(TEST_DOCUMENT)


def test_vector_normalization(index_operation, mock_vector_service):
    """
    Test vector normalization.

    Given: Vector service returns unnormalized vector
    When: Preparing the document
    Then: Vector should be normalized correctly
    """
    # Return unnormalized vector
    mock_vector_service.encode.return_value = np.array([[1.0, 2.0, 2.0]])

    prepared = index_operation.prepare_document(TEST_DOCUMENT)

    vector = prepared["vector"]
    # Check if vector is normalized (length should be close to 1)
    length = sum(x * x for x in vector) ** 0.5
    assert abs(length - 1.0) < 1e-6, "Vector should be normalized"


def test_vector_dimensionality(index_operation, mock_vector_service):
    """
    Test vector dimensionality validation.

    Given: Vector service returns vector with wrong dimensions
    When: Preparing the document
    Then: Appropriate error should be raised
    """
    # Return vector with wrong dimensions
    mock_vector_service.encode.return_value = np.array(
        [[0.1] * 768]
    )  # Assuming expected dim is different

    with pytest.raises(VectorEncodingError, match="Invalid vector dimensionality"):
        index_operation.prepare_document(TEST_DOCUMENT)
