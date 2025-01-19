"""Integration tests for document management endpoints.

Tests the document upload, retrieval, listing, and deletion functionality
through the API endpoints.
"""

import json
from pathlib import Path
from typing import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from src.api.models.requests import DocumentUploadResponse
from src.api.repositories.weaviate_repo import WeaviateRepository
from src.api.services.document import DocumentService
from tests.fixtures.documents import create_test_document


@pytest.fixture
async def test_app(weaviate_client) -> FastAPI:
    """Create test application with dependencies."""
    from src.api.dependencies.weaviate import get_weaviate_client
    from src.api.main import app

    async def override_get_weaviate_client():
        return weaviate_client

    app.dependency_overrides[get_weaviate_client] = override_get_weaviate_client
    return app


@pytest.fixture
async def client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_document(tmp_path) -> Path:
    """Create a test document."""
    return await create_test_document(
        tmp_path / "test.docx",
        content="Test content for API integration testing",
        metadata={"author": "Test Author", "created": "2024-01-01"},
    )


@pytest.mark.asyncio
async def test_upload_document(client: AsyncClient, test_document: Path):
    """Test document upload endpoint."""
    # Prepare file for upload
    files = {
        "file": (
            test_document.name,
            test_document.open("rb"),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }

    # Upload document
    response = await client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 200

    result = response.json()
    assert result["status"] == "success"
    assert result["file_name"] == test_document.name
    assert result["file_type"] == ".docx"
    assert result["document_id"] is not None


@pytest.mark.asyncio
async def test_batch_upload_documents(client: AsyncClient, tmp_path: Path):
    """Test batch document upload endpoint."""
    # Create multiple test documents
    docs = []
    for i in range(3):
        doc = await create_test_document(
            tmp_path / f"test_{i}.docx",
            content=f"Test content {i}",
            metadata={"index": i},
        )
        docs.append(doc)

    # Prepare files for upload
    files = [
        (
            "files",
            (
                doc.name,
                doc.open("rb"),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        )
        for doc in docs
    ]

    # Upload documents
    response = await client.post("/api/v1/documents/upload/batch", files=files)
    assert response.status_code == 200

    results = response.json()
    assert len(results) == len(docs)
    assert all(result["status"] == "success" for result in results)
    assert all(result["document_id"] is not None for result in results)


@pytest.mark.asyncio
async def test_list_documents(
    client: AsyncClient,
    test_document: Path,
):
    """Test document listing endpoint."""
    # First upload a document
    files = {
        "file": (
            test_document.name,
            test_document.open("rb"),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    upload_response = await client.post("/api/v1/documents/upload", files=files)
    assert upload_response.status_code == 200

    # List documents
    response = await client.get("/api/v1/documents/")
    assert response.status_code == 200

    documents = response.json()
    assert len(documents) > 0
    assert any(doc["title"] == test_document.name for doc in documents)

    # Test pagination
    response = await client.get("/api/v1/documents/?limit=1")
    assert response.status_code == 200
    assert len(response.json()) == 1

    # Test file type filter
    response = await client.get("/api/v1/documents/?file_type=docx")
    assert response.status_code == 200
    assert all(doc["file_type"] == ".docx" for doc in response.json())


@pytest.mark.asyncio
async def test_get_document(
    client: AsyncClient,
    test_document: Path,
):
    """Test document retrieval endpoint."""
    # First upload a document
    files = {
        "file": (
            test_document.name,
            test_document.open("rb"),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    upload_response = await client.post("/api/v1/documents/upload", files=files)
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    # Get document
    response = await client.get(f"/api/v1/documents/{document_id}")
    assert response.status_code == 200

    document = response.json()
    assert document["title"] == test_document.name
    assert document["file_type"] == ".docx"
    assert "content" in document
    assert "metadata" in document


@pytest.mark.asyncio
async def test_delete_document(
    client: AsyncClient,
    test_document: Path,
):
    """Test document deletion endpoint."""
    # First upload a document
    files = {
        "file": (
            test_document.name,
            test_document.open("rb"),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    upload_response = await client.post("/api/v1/documents/upload", files=files)
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    # Delete document
    response = await client.delete(f"/api/v1/documents/{document_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Verify document is deleted
    response = await client.get(f"/api/v1/documents/{document_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_document_stats(
    client: AsyncClient,
    test_document: Path,
):
    """Test document statistics endpoint."""
    # First upload a document
    files = {
        "file": (
            test_document.name,
            test_document.open("rb"),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    await client.post("/api/v1/documents/upload", files=files)

    # Get stats
    response = await client.get("/api/v1/documents/stats/summary")
    assert response.status_code == 200

    stats = response.json()
    assert "total_documents" in stats
    assert "file_types" in stats
    assert stats["total_documents"] > 0
    assert ".docx" in stats["file_types"]


@pytest.mark.asyncio
async def test_download_document(
    client: AsyncClient,
    test_document: Path,
):
    """Test document download endpoint."""
    # First upload a document
    files = {
        "file": (
            test_document.name,
            test_document.open("rb"),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    upload_response = await client.post("/api/v1/documents/upload", files=files)
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    # Download document
    response = await client.get(f"/api/v1/documents/{document_id}/download")
    assert response.status_code == 200
    assert (
        response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert len(response.content) > 0
