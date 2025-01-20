"""Performance tests for storage strategies.

This module contains performance benchmarks and validation tests for storage strategies,
including tests for:
- Basic operation latency (save, load, delete)
- Batch operation throughput
- Concurrent operation performance
- Memory usage patterns
- Disk I/O patterns (for file-based storage)
"""

import asyncio
import time
from uuid import UUID

import pytest

from src.core.models.documents import Document
from src.core.storage.strategies.json_storage import JsonStorage
from src.core.storage.strategies.memory_storage import MemoryStorage
from src.core.types.storage import StorageStrategy


@pytest.fixture
def sample_documents(size: int = 1000) -> list[Document]:
    """Create a list of sample documents for testing."""
    return [
        Document(id=UUID(int=i), content=f"Test document {i}", metadata={"test_key": f"value_{i}"})
        for i in range(size)
    ]


@pytest.fixture(params=[JsonStorage, MemoryStorage])
def storage_strategy(request, tmp_path) -> StorageStrategy:
    """Provide storage strategy instances for testing."""
    if request.param == JsonStorage:
        return JsonStorage(storage_dir=tmp_path)
    return MemoryStorage()


async def test_single_operation_latency(storage_strategy, sample_documents):
    """Test latency of individual storage operations."""
    doc = sample_documents[0]

    # Test save latency
    start = time.perf_counter()
    await storage_strategy.save(doc.id, doc)
    save_duration = time.perf_counter() - start
    assert save_duration < 0.1, f"Save operation took {save_duration:.3f}s"

    # Test load latency
    start = time.perf_counter()
    loaded_doc = await storage_strategy.load(doc.id)
    load_duration = time.perf_counter() - start
    assert load_duration < 0.1, f"Load operation took {load_duration:.3f}s"
    assert loaded_doc == doc

    # Test delete latency
    start = time.perf_counter()
    await storage_strategy.delete(doc.id)
    delete_duration = time.perf_counter() - start
    assert delete_duration < 0.1, f"Delete operation took {delete_duration:.3f}s"


async def test_batch_operation_throughput(storage_strategy, sample_documents):
    """Test throughput of batch operations."""
    batch_size = 100
    docs = sample_documents[:batch_size]

    # Test batch save throughput
    start = time.perf_counter()
    await asyncio.gather(*[storage_strategy.save(doc.id, doc) for doc in docs])
    save_duration = time.perf_counter() - start

    throughput = batch_size / save_duration
    assert throughput > 50, f"Batch save throughput: {throughput:.1f} ops/sec"

    # Test batch load throughput
    start = time.perf_counter()
    loaded_docs = await asyncio.gather(*[storage_strategy.load(doc.id) for doc in docs])
    load_duration = time.perf_counter() - start

    throughput = batch_size / load_duration
    assert throughput > 50, f"Batch load throughput: {throughput:.1f} ops/sec"
    assert all(a == b for a, b in zip(loaded_docs, docs, strict=False))


async def test_concurrent_operation_performance(storage_strategy, sample_documents):
    """Test performance under concurrent operations."""
    num_concurrent = 10
    docs_per_task = 50

    async def concurrent_task(docs):
        for doc in docs:
            await storage_strategy.save(doc.id, doc)
            loaded = await storage_strategy.load(doc.id)
            assert loaded == doc
            await storage_strategy.delete(doc.id)

    # Split documents among tasks
    doc_chunks = [
        sample_documents[i : i + docs_per_task]
        for i in range(0, num_concurrent * docs_per_task, docs_per_task)
    ]

    start = time.perf_counter()
    await asyncio.gather(*[concurrent_task(chunk) for chunk in doc_chunks])
    duration = time.perf_counter() - start

    total_ops = num_concurrent * docs_per_task * 3  # save, load, delete
    throughput = total_ops / duration
    assert throughput > 100, f"Concurrent throughput: {throughput:.1f} ops/sec"


async def test_memory_usage_pattern(storage_strategy, sample_documents):
    """Test memory usage patterns during operations."""
    import os

    import psutil

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss

    # Test memory usage during batch save
    await asyncio.gather(*[storage_strategy.save(doc.id, doc) for doc in sample_documents[:500]])

    peak_memory = process.memory_info().rss
    memory_increase = peak_memory - initial_memory
    memory_per_doc = memory_increase / 500

    # Memory increase should be reasonable (less than 10KB per document)
    assert memory_per_doc < 10 * 1024, f"Memory usage per document: {memory_per_doc / 1024:.1f}KB"
