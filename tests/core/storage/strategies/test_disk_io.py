"""Disk I/O tests for JSON storage strategy.

This module contains tests specifically focused on disk I/O patterns and performance
for the JSON storage strategy, including:
- File creation and deletion patterns
- Disk space usage
- I/O operation batching
- File system load under concurrent operations
"""

import asyncio
import os
import time
from pathlib import Path
from typing import List
from uuid import UUID

import pytest

from src.core.models.documents import Document
from src.core.storage.strategies.json_storage import JsonStorage


@pytest.fixture
def sample_documents(size: int = 1000) -> List[Document]:
    """Create a list of sample documents for testing."""
    return [
        Document(
            id=UUID(int=i),
            content=f"Test document {i} with some additional content to ensure realistic file sizes",
            metadata={"test_key": f"value_{i}", "timestamp": time.time()},
        )
        for i in range(size)
    ]


@pytest.fixture
def json_storage(tmp_path) -> JsonStorage:
    """Create a JSON storage instance for testing."""
    return JsonStorage(storage_dir=tmp_path)


async def test_file_operation_patterns(json_storage, sample_documents):
    """Test file creation and deletion patterns."""
    doc = sample_documents[0]
    storage_path = Path(json_storage._storage_dir)

    # Test file creation
    await json_storage.save(doc.id, doc)
    expected_file = storage_path / f"{doc.id}.json"
    assert expected_file.exists(), "File was not created"

    # Test file content
    file_size = expected_file.stat().st_size
    assert file_size > 0, "File is empty"
    assert file_size < 10 * 1024, "File size exceeds 10KB"

    # Test file deletion
    await json_storage.delete(doc.id)
    assert not expected_file.exists(), "File was not deleted"


async def test_disk_space_usage(json_storage, sample_documents):
    """Test disk space usage patterns."""
    storage_path = Path(json_storage._storage_dir)
    initial_size = sum(f.stat().st_size for f in storage_path.glob("*.json"))

    # Save batch of documents
    batch_size = 100
    docs = sample_documents[:batch_size]
    await asyncio.gather(*[json_storage.save(doc.id, doc) for doc in docs])

    # Check disk usage
    final_size = sum(f.stat().st_size for f in storage_path.glob("*.json"))
    size_increase = final_size - initial_size
    size_per_doc = size_increase / batch_size

    # Average file size should be reasonable (less than 5KB per document)
    assert size_per_doc < 5 * 1024, f"Average file size: {size_per_doc / 1024:.1f}KB"


async def test_io_operation_batching(json_storage, sample_documents):
    """Test I/O operation batching performance."""
    batch_sizes = [1, 10, 50, 100]
    results = {}

    for batch_size in batch_sizes:
        docs = sample_documents[:batch_size]

        # Measure batch save time
        start = time.perf_counter()
        await asyncio.gather(*[json_storage.save(doc.id, doc) for doc in docs])
        duration = time.perf_counter() - start

        results[batch_size] = duration / batch_size

    # Verify that larger batches have better per-operation performance
    assert all(
        results[batch_sizes[i]] > results[batch_sizes[i + 1]] for i in range(len(batch_sizes) - 1)
    ), "Larger batches should be more efficient per operation"


async def test_concurrent_io_load(json_storage, sample_documents):
    """Test file system performance under concurrent I/O load."""
    num_concurrent = 5
    docs_per_task = 20

    async def io_task(docs):
        for doc in docs:
            await json_storage.save(doc.id, doc)
            await asyncio.sleep(0.01)  # Simulate real-world delays
            await json_storage.load(doc.id)
            await json_storage.delete(doc.id)

    # Split documents among tasks
    doc_chunks = [
        sample_documents[i : i + docs_per_task]
        for i in range(0, num_concurrent * docs_per_task, docs_per_task)
    ]

    start = time.perf_counter()
    await asyncio.gather(*[io_task(chunk) for chunk in doc_chunks])
    duration = time.perf_counter() - start

    # Calculate IOPS (I/O operations per second)
    total_ops = num_concurrent * docs_per_task * 3  # save, load, delete
    iops = total_ops / duration

    # Ensure reasonable IOPS (at least 10 ops/sec with artificial delays)
    assert iops > 10, f"IOPS: {iops:.1f}"
