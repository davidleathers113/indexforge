"""Integration tests for API performance and resource management.

Tests API performance characteristics including response times,
concurrent requests, and resource utilization.
"""

import asyncio
import time
from pathlib import Path
from typing import AsyncGenerator, List

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from src.api.models.requests import SearchQuery
from src.core.metrics import MemoryTracker, TimeTracker
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
    for i in range(10):  # Create 10 test documents
        doc = await create_test_document(
            tmp_path / f"test_{i}.docx",
            content=f"Test content {i} with some meaningful text for performance testing",
            metadata={"index": i},
        )
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
async def test_response_times(client: AsyncClient, test_documents: List[dict]):
    """Test API endpoint response times."""
    time_tracker = TimeTracker()

    # Test document listing
    with time_tracker:
        response = await client.get("/api/v1/documents/")
        assert response.status_code == 200
    list_time = time_tracker.elapsed_seconds
    assert list_time < 1.0  # Should respond within 1 second

    # Test document retrieval
    doc_id = test_documents[0]["document_id"]
    with time_tracker:
        response = await client.get(f"/api/v1/documents/{doc_id}")
        assert response.status_code == 200
    get_time = time_tracker.elapsed_seconds
    assert get_time < 0.5  # Should respond within 0.5 seconds

    # Test search
    query = SearchQuery(query="test content", limit=5)
    with time_tracker:
        response = await client.post("/api/v1/search", json=query.dict())
        assert response.status_code == 200
    search_time = time_tracker.elapsed_seconds
    assert search_time < 2.0  # Search should complete within 2 seconds


@pytest.mark.asyncio
async def test_concurrent_requests(
    client: AsyncClient,
    test_documents: List[dict],
    tmp_path: Path,
):
    """Test handling of concurrent API requests."""
    time_tracker = TimeTracker()
    doc_ids = [doc["document_id"] for doc in test_documents]

    # Prepare concurrent requests
    async def get_document(doc_id: str) -> dict:
        response = await client.get(f"/api/v1/documents/{doc_id}")
        assert response.status_code == 200
        return response.json()

    # Execute concurrent document retrievals
    with time_tracker:
        results = await asyncio.gather(*(get_document(doc_id) for doc_id in doc_ids))
    total_time = time_tracker.elapsed_seconds

    # Verify results
    assert len(results) == len(doc_ids)
    assert all(isinstance(result, dict) for result in results)
    # Total time should be significantly less than sequential execution
    assert total_time < 0.5 * len(doc_ids)

    # Test concurrent uploads
    async def upload_document(index: int) -> dict:
        doc = await create_test_document(
            tmp_path / f"concurrent_{index}.docx",
            content=f"Concurrent test content {index}",
        )
        files = {
            "file": (
                doc.name,
                doc.open("rb"),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }
        response = await client.post("/api/v1/documents/upload", files=files)
        assert response.status_code == 200
        return response.json()

    # Execute concurrent uploads
    with time_tracker:
        upload_results = await asyncio.gather(*(upload_document(i) for i in range(5)))
    upload_time = time_tracker.elapsed_seconds

    # Verify upload results
    assert len(upload_results) == 5
    assert all(result["status"] == "success" for result in upload_results)
    assert upload_time < 2.5  # Should complete within 2.5 seconds


@pytest.mark.asyncio
async def test_memory_usage(client: AsyncClient, test_documents: List[dict]):
    """Test memory usage during API operations."""
    memory_tracker = MemoryTracker()
    doc_ids = [doc["document_id"] for doc in test_documents]

    # Record baseline memory
    baseline_memory = memory_tracker.get_memory_mb()

    # Test memory during batch operations
    async def process_document(doc_id: str):
        response = await client.get(f"/api/v1/documents/{doc_id}")
        assert response.status_code == 200
        return response.json()

    # Execute batch processing
    results = await asyncio.gather(*(process_document(doc_id) for doc_id in doc_ids))
    peak_memory = memory_tracker.get_peak_memory_mb()

    # Verify memory usage
    assert len(results) == len(doc_ids)
    memory_increase = peak_memory - baseline_memory
    assert memory_increase < 100  # Should use less than 100MB additional memory

    # Verify cleanup
    await asyncio.sleep(0.1)  # Allow time for cleanup
    end_memory = memory_tracker.get_memory_mb()
    assert abs(end_memory - baseline_memory) < 10  # Memory should return close to baseline


@pytest.mark.asyncio
async def test_resource_limits(client: AsyncClient, tmp_path: Path):
    """Test API behavior under resource constraints."""

    # Test with large number of concurrent requests
    async def make_request(i: int) -> dict:
        response = await client.get("/api/v1/documents/")
        assert response.status_code in (200, 429)  # Accept either success or rate limit
        return response.status_code

    # Execute many concurrent requests
    results = await asyncio.gather(*(make_request(i) for i in range(50)))

    # Verify rate limiting
    success_count = sum(1 for status in results if status == 200)
    rate_limited = sum(1 for status in results if status == 429)
    assert success_count > 0  # Some requests should succeed
    assert rate_limited >= 0  # Some requests might be rate limited

    # Test with large search result set
    query = SearchQuery(query="test", limit=100)  # Request large result set
    response = await client.post("/api/v1/search", json=query.dict())
    assert response.status_code == 200
    results = response.json()

    # Verify result limiting
    assert len(results["results"]) <= 100  # Should respect limit
    assert "total" in results  # Should include total count


@pytest.mark.asyncio
async def test_endpoint_stability(client: AsyncClient):
    """Test API endpoint stability over time."""
    request_times = []
    error_count = 0

    # Make requests over a period
    for _ in range(10):  # 10 iterations
        try:
            with TimeTracker() as tracker:
                response = await client.get("/api/v1/documents/")
                assert response.status_code == 200
            request_times.append(tracker.elapsed_seconds)
        except Exception:
            error_count += 1
        await asyncio.sleep(0.1)  # 100ms between requests

    # Calculate statistics
    avg_time = sum(request_times) / len(request_times)
    max_time = max(request_times)

    # Verify stability
    assert error_count == 0  # No errors should occur
    assert avg_time < 1.0  # Average response time under 1 second
    assert max_time < 2.0  # Maximum response time under 2 seconds
