"""Tests for DocumentRetrievalService."""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from src.api.services.document_retrieval_service import DocumentRetrievalService


@pytest.mark.asyncio
async def test_list_documents(
    document_retrieval_service: DocumentRetrievalService,
    mock_repository: AsyncMock,
):
    """Test listing documents."""
    mock_repository.list_documents.return_value = [
        {"id": "1", "title": "doc1"},
        {"id": "2", "title": "doc2"},
    ]

    result = await document_retrieval_service.list_documents(file_type=None, limit=10, offset=0)

    assert len(result) == 2
    mock_repository.list_documents.assert_called_once_with(None, 10, 0)


@pytest.mark.asyncio
async def test_get_document_success(
    document_retrieval_service: DocumentRetrievalService,
    mock_repository: AsyncMock,
):
    """Test getting a document successfully."""
    doc_id = "test-id"
    mock_repository.get_document.return_value = {"id": doc_id, "title": "test"}

    result = await document_retrieval_service.get_document(doc_id)

    assert result["id"] == doc_id
    mock_repository.get_document.assert_called_once_with(doc_id)


@pytest.mark.asyncio
async def test_get_document_not_found(
    document_retrieval_service: DocumentRetrievalService,
    mock_repository: AsyncMock,
):
    """Test getting a non-existent document."""
    mock_repository.get_document.return_value = None

    result = await document_retrieval_service.get_document("non-existent")

    assert result is None
    mock_repository.get_document.assert_called_once()


@pytest.mark.asyncio
async def test_delete_document_success(
    document_retrieval_service: DocumentRetrievalService,
    mock_repository: AsyncMock,
):
    """Test deleting a document successfully."""
    doc_id = "test-id"
    mock_repository.delete_document.return_value = True

    result = await document_retrieval_service.delete_document(doc_id)

    assert result is True
    mock_repository.delete_document.assert_called_once_with(doc_id)


@pytest.mark.asyncio
async def test_delete_document_not_found(
    document_retrieval_service: DocumentRetrievalService,
    mock_repository: AsyncMock,
):
    """Test deleting a non-existent document."""
    mock_repository.delete_document.return_value = False

    result = await document_retrieval_service.delete_document("non-existent")

    assert result is False
    mock_repository.delete_document.assert_called_once()


@pytest.mark.asyncio
async def test_download_document_success(
    document_retrieval_service: DocumentRetrievalService,
    mock_repository: AsyncMock,
):
    """Test downloading a document successfully."""
    doc_id = "test-id"
    mock_repository.get_document.return_value = {
        "title": "test.txt",
        "file_path": "test.txt",
    }
    mock_repository.get_document_content.return_value = b"test content"

    response = await document_retrieval_service.download_document(doc_id)

    assert response.media_type == "text/plain"
    assert "test.txt" in response.headers["Content-Disposition"]
    mock_repository.get_document.assert_called_once_with(doc_id)
    mock_repository.get_document_content.assert_called_once_with(doc_id)


@pytest.mark.asyncio
async def test_download_document_not_found(
    document_retrieval_service: DocumentRetrievalService,
    mock_repository: AsyncMock,
):
    """Test downloading a non-existent document."""
    mock_repository.get_document.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await document_retrieval_service.download_document("non-existent")

    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_download_document_content_not_found(
    document_retrieval_service: DocumentRetrievalService,
    mock_repository: AsyncMock,
):
    """Test downloading a document with missing content."""
    doc_id = "test-id"
    mock_repository.get_document.return_value = {
        "title": "test.txt",
        "file_path": "test.txt",
    }
    mock_repository.get_document_content.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await document_retrieval_service.download_document(doc_id)

    assert exc_info.value.status_code == 404
    assert "content not found" in str(exc_info.value.detail).lower()
