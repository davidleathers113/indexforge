"""Integration tests for storage system components.

This module contains integration tests that verify the correct interaction between
repositories, storage strategies, and metrics collection. Tests include:
- Cross-component operations
- End-to-end document flows
- Error propagation
- Metrics collection during operations
- Performance under realistic usage patterns
"""

import asyncio
from datetime import UTC, datetime
from typing import AsyncGenerator
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel

from src.core.models.documents import Document
from src.core.storage.metrics.collector import MetricsCollector
from src.core.storage.metrics.models import OperationMetrics
from src.core.storage.repositories.documents import DocumentRepository
from src.core.storage.repositories.lineage import LineageRepository
from src.core.storage.strategies.memory_storage import MemoryStorage


class TestDocument(BaseModel):
    """Test document model."""

    id: UUID
    content: str
    created_at: datetime = datetime.now(UTC)
    metadata: dict = {}


@pytest.fixture
async def metrics_collector(tmp_path) -> MetricsCollector:
    """Create a metrics collector for testing."""
    collector = MetricsCollector(storage_path=tmp_path)
    yield collector
    await collector.clear_metrics()


@pytest.fixture
async def document_repo(metrics_collector) -> AsyncGenerator[DocumentRepository, None]:
    """Create a document repository with memory storage."""
    storage = MemoryStorage()
    repo = DocumentRepository(storage=storage, metrics_collector=metrics_collector)
    yield repo
    await storage.clear()


@pytest.fixture
async def lineage_repo(metrics_collector) -> AsyncGenerator[LineageRepository, None]:
    """Create a lineage repository with memory storage."""
    storage = MemoryStorage()
    repo = LineageRepository(storage=storage, metrics_collector=metrics_collector)
    yield repo
    await storage.clear()


async def test_cross_repository_operations(document_repo, lineage_repo):
    """Test interactions between document and lineage repositories."""
    # Create and store a document
    doc_id = uuid4()
    doc = TestDocument(id=doc_id, content="Test document")
    await document_repo.save(doc)

    # Create lineage for the document
    lineage = await lineage_repo.create_lineage(doc_id)
    assert lineage is not None
    assert lineage.doc_id == doc_id
    assert lineage.created_at is not None

    # Verify document exists in both repositories
    stored_doc = await document_repo.get(doc_id)
    assert stored_doc == doc

    stored_lineage = await lineage_repo.get_lineage(doc_id)
    assert stored_lineage is not None
    assert stored_lineage.doc_id == doc_id

    # Delete document and verify cascading effects
    await document_repo.delete(doc_id)
    assert await document_repo.get(doc_id) is None
    assert await lineage_repo.get_lineage(doc_id) is None


async def test_metrics_collection(document_repo, metrics_collector):
    """Test metrics collection during repository operations."""
    # Perform operations
    doc_id = uuid4()
    doc = TestDocument(id=doc_id, content="Test document")
    await document_repo.save(doc)
    await document_repo.get(doc_id)
    await document_repo.delete(doc_id)

    # Verify metrics
    metrics = metrics_collector.get_recent_metrics()
    assert len(metrics) == 3  # save, get, delete operations

    # Check operation types
    operation_types = [m.operation_type for m in metrics]
    assert "save" in operation_types
    assert "get" in operation_types
    assert "delete" in operation_types

    # Verify all operations were successful
    assert all(m.success for m in metrics)


async def test_error_propagation(document_repo):
    """Test error propagation across components."""
    # Attempt to get nonexistent document
    missing_id = uuid4()
    result = await document_repo.get(missing_id)
    assert result is None

    # Attempt to delete nonexistent document
    await document_repo.delete(missing_id)  # Should not raise

    # Attempt to save document with same ID
    doc_id = uuid4()
    doc = TestDocument(id=doc_id, content="Test document")
    await document_repo.save(doc)

    with pytest.raises(ValueError):
        await document_repo.save(doc)  # Should raise for duplicate


async def test_concurrent_repository_access(document_repo):
    """Test concurrent access to repositories."""
    num_docs = 50
    docs = [TestDocument(id=uuid4(), content=f"Test document {i}") for i in range(num_docs)]

    # Concurrent saves
    await asyncio.gather(*[document_repo.save(doc) for doc in docs])

    # Concurrent gets
    stored_docs = await asyncio.gather(*[document_repo.get(doc.id) for doc in docs])
    assert all(a == b for a, b in zip(stored_docs, docs))

    # Concurrent deletes
    await asyncio.gather(*[document_repo.delete(doc.id) for doc in docs])
    assert all(not (await document_repo.exists(doc.id)) for doc in docs)


async def test_repository_performance(document_repo, metrics_collector):
    """Test repository performance under load."""
    num_docs = 100
    docs = [TestDocument(id=uuid4(), content=f"Test document {i}") for i in range(num_docs)]

    # Measure batch save performance
    start = asyncio.get_event_loop().time()
    await asyncio.gather(*[document_repo.save(doc) for doc in docs])
    duration = asyncio.get_event_loop().time() - start

    # Verify throughput meets requirements
    throughput = num_docs / duration
    assert throughput > 50, f"Save throughput: {throughput:.1f} ops/sec"

    # Check operation latencies in metrics
    metrics = metrics_collector.get_recent_metrics()
    save_latencies = [m.duration_ms for m in metrics if m.operation_type == "save"]
    avg_latency = sum(save_latencies) / len(save_latencies)
    assert avg_latency < 100, f"Average save latency: {avg_latency:.1f}ms"
