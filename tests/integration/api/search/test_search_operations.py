"""Integration tests for search operations.

Tests the document search functionality, including semantic search,
filtering, and result ranking.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncGenerator, List

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


@pytest.fixture
async def test_documents(client: AsyncClient, tmp_path: Path) -> List[dict]:
    """Create and upload test documents."""
    documents = []
    contents = [
        "Machine learning is a subset of artificial intelligence",
        "Python is a popular programming language",
        "Data science involves statistical analysis",
        "Neural networks are used in deep learning",
    ]

    for i, content in enumerate(contents):
        doc = await create_test_document(
            tmp_path / f"test_{i}.docx",
            content=content,
            metadata={
                "author": f"Author {i}",
                "created": (datetime.now() - timedelta(days=i)).isoformat(),
                "keywords": ["test", f"keyword_{i}"],
            },
        )

        # Upload document
        files = {
            "file": (
                doc.name,
                doc.open("rb"),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }
        response = await client.post("/api/v1/documents/upload", files=files)
        assert response.status_code == 200
        documents.append(response.json())

    return documents


@pytest.mark.asyncio
async def test_semantic_search(client: AsyncClient, test_documents: List[dict]):
    """Test semantic search functionality."""
    # Search for documents about machine learning
    query = SearchQuery(
        query="What documents are about machine learning?",
        limit=2,
    )
    response = await client.post(
        "/api/v1/search",
        json=query.dict(),
    )
    assert response.status_code == 200

    results = response.json()
    assert len(results["results"]) > 0
    # First result should be about machine learning
    assert "machine learning" in results["results"][0]["content"].lower()
    assert results["total"] > 0
    assert results["took"] > 0


@pytest.mark.asyncio
async def test_filtered_search(client: AsyncClient, test_documents: List[dict]):
    """Test search with filters."""
    # Search with file type filter
    query = SearchQuery(query="programming")
    filter_params = DocumentFilter(file_type="docx")

    response = await client.post(
        "/api/v1/search",
        json={
            **query.dict(),
            "filter": filter_params.dict(),
        },
    )
    assert response.status_code == 200

    results = response.json()
    assert len(results["results"]) > 0
    assert all(result["file_type"] == ".docx" for result in results["results"])
    # Top result should be about Python programming
    assert "python" in results["results"][0]["content"].lower()


@pytest.mark.asyncio
async def test_search_pagination(client: AsyncClient, test_documents: List[dict]):
    """Test search result pagination."""
    # First page
    query = SearchQuery(query="test", limit=2, offset=0)
    response = await client.post(
        "/api/v1/search",
        json=query.dict(),
    )
    assert response.status_code == 200
    first_page = response.json()
    assert len(first_page["results"]) == 2

    # Second page
    query.offset = 2
    response = await client.post(
        "/api/v1/search",
        json=query.dict(),
    )
    assert response.status_code == 200
    second_page = response.json()

    # Verify different results
    first_ids = {r["id"] for r in first_page["results"]}
    second_ids = {r["id"] for r in second_page["results"]}
    assert not first_ids.intersection(second_ids)


@pytest.mark.asyncio
async def test_search_ranking(client: AsyncClient, test_documents: List[dict]):
    """Test search result ranking."""
    # Search for a specific topic
    query = SearchQuery(query="deep learning neural networks")
    response = await client.post(
        "/api/v1/search",
        json=query.dict(),
    )
    assert response.status_code == 200

    results = response.json()
    # The document about neural networks should be ranked higher
    assert any("neural networks" in result["content"].lower() for result in results["results"][:2])


@pytest.mark.asyncio
async def test_search_with_date_filter(client: AsyncClient, test_documents: List[dict]):
    """Test search with date filtering."""
    yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
    tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()

    query = SearchQuery(query="test")
    filter_params = DocumentFilter(
        date_from=yesterday,
        date_to=tomorrow,
    )

    response = await client.post(
        "/api/v1/search",
        json={
            **query.dict(),
            "filter": filter_params.dict(),
        },
    )
    assert response.status_code == 200

    results = response.json()
    assert len(results["results"]) > 0
    # Verify documents are within date range
    for result in results["results"]:
        doc_date = datetime.fromisoformat(result["metadata"]["created"]).date()
        assert yesterday <= doc_date.isoformat() <= tomorrow


@pytest.mark.asyncio
async def test_empty_search_results(client: AsyncClient, test_documents: List[dict]):
    """Test search with no matching results."""
    query = SearchQuery(
        query="xyzabc123 nonexistent content",
        limit=10,
    )
    response = await client.post(
        "/api/v1/search",
        json=query.dict(),
    )
    assert response.status_code == 200

    results = response.json()
    assert len(results["results"]) == 0
    assert results["total"] == 0
