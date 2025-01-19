"""Integration tests for API error handling.

Tests various error scenarios and validates error responses
across different API endpoints.
"""

import io
from pathlib import Path
from typing import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from src.api.models.requests import DocumentFilter, SearchQuery
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


@pytest.mark.asyncio
async def test_invalid_file_type(client: AsyncClient):
    """Test upload with invalid file type."""
    # Create invalid file
    content = io.BytesIO(b"Invalid file content")
    files = {"file": ("test.xyz", content, "application/octet-stream")}

    response = await client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_file_size_limit(client: AsyncClient):
    """Test upload exceeding file size limit."""
    # Create large file (11MB)
    content = io.BytesIO(b"0" * (11 * 1024 * 1024))
    files = {
        "file": (
            "large.docx",
            content,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }

    response = await client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 400
    assert "exceeds maximum limit" in response.json()["detail"]


@pytest.mark.asyncio
async def test_invalid_document_id(client: AsyncClient):
    """Test operations with invalid document ID."""
    invalid_id = "nonexistent_id"

    # Test get document
    response = await client.get(f"/api/v1/documents/{invalid_id}")
    assert response.status_code == 404
    assert "Document not found" in response.json()["detail"]

    # Test delete document
    response = await client.delete(f"/api/v1/documents/{invalid_id}")
    assert response.status_code == 404
    assert "Document not found" in response.json()["detail"]

    # Test download document
    response = await client.get(f"/api/v1/documents/{invalid_id}/download")
    assert response.status_code == 404
    assert "Document not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_invalid_search_query(client: AsyncClient):
    """Test search with invalid query parameters."""
    # Empty query
    response = await client.post(
        "/api/v1/search",
        json={"query": "", "limit": 10},
    )
    assert response.status_code == 422

    # Invalid limit
    response = await client.post(
        "/api/v1/search",
        json={"query": "test", "limit": -1},
    )
    assert response.status_code == 422

    # Invalid offset
    response = await client.post(
        "/api/v1/search",
        json={"query": "test", "limit": 10, "offset": -1},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_filter_parameters(client: AsyncClient):
    """Test search with invalid filter parameters."""
    # Invalid date format
    query = SearchQuery(query="test")
    filter_params = DocumentFilter(
        date_from="invalid-date",
        date_to="2024-13-45",  # Invalid date
    )

    response = await client.post(
        "/api/v1/search",
        json={
            **query.dict(),
            "filter": filter_params.dict(),
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_malformed_request(client: AsyncClient):
    """Test handling of malformed requests."""
    # Invalid JSON
    response = await client.post(
        "/api/v1/search",
        content=b"invalid json content",
    )
    assert response.status_code == 422

    # Missing required fields
    response = await client.post(
        "/api/v1/search",
        json={},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_concurrent_delete(client: AsyncClient, test_document: Path):
    """Test concurrent deletion of the same document."""
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
    response1 = await client.delete(f"/api/v1/documents/{document_id}")
    assert response1.status_code == 200

    # Try to delete again
    response2 = await client.delete(f"/api/v1/documents/{document_id}")
    assert response2.status_code == 404


@pytest.mark.asyncio
async def test_invalid_batch_upload(client: AsyncClient):
    """Test batch upload with invalid files."""
    # Create mixed valid and invalid files
    files = [
        ("files", ("test1.xyz", io.BytesIO(b"Invalid content"), "application/octet-stream")),
        (
            "files",
            (
                "test2.docx",
                io.BytesIO(b"Valid content"),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        ),
    ]

    response = await client.post("/api/v1/documents/upload/batch", files=files)
    assert response.status_code == 200
    results = response.json()

    # Verify mixed results
    assert len(results) == 2
    assert any(r["status"] == "error" for r in results)
    assert any(r["status"] == "success" for r in results)
