"""Integration tests for storage service performance.

This module provides performance benchmarks for storage services,
measuring throughput, latency, and resource usage under various loads.
"""

import asyncio
import gc
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional, Tuple
from uuid import UUID

import psutil
import pytest
from pytest_asyncio import fixture

from src.core.models.chunks import Chunk
from src.core.models.documents import Document
from src.core.models.references import Reference
from src.core.settings import Settings
from src.services.storage import (
    BatchConfig,
    ChunkStorageService,
    DocumentStorageService,
    ReferenceStorageService,
)
from tests.integration.services.builders.test_data import (
    ChunkBuilder,
    DocumentBuilder,
    ReferenceBuilder,
)


@dataclass
class OperationMetrics:
    """Metrics for a single operation."""

    operation: str
    duration_ms: float
    memory_mb: float
    throughput: float
    success: bool
    error: Optional[str] = None


@dataclass
class TestReport:
    """Performance test report."""

    test_name: str
    start_time: float
    end_time: float
    total_duration: float
    operations: List[OperationMetrics]
    peak_memory_mb: float
    avg_memory_mb: float
    total_operations: int
    successful_operations: int
    failed_operations: int

    def to_dict(self) -> Dict:
        """Convert report to dictionary."""
        return asdict(self)

    def save(self, path: Path):
        """Save report to file."""
        with path.open("w") as f:
            json.dump(self.to_dict(), f, indent=2)


class MemoryMonitor:
    """Monitor memory usage during operations."""

    def __init__(self):
        """Initialize the memory monitor."""
        self.process = psutil.Process()
        self.measurements = []
        self.peak_memory = 0
        gc.collect()  # Clean up before monitoring

    def measure(self) -> float:
        """Measure current memory usage in MB."""
        gc.collect()  # Ensure garbage is collected
        memory_mb = self.process.memory_info().rss / (1024 * 1024)
        self.measurements.append(memory_mb)
        self.peak_memory = max(self.peak_memory, memory_mb)
        return memory_mb

    @property
    def avg_memory(self) -> float:
        """Get average memory usage in MB."""
        return sum(self.measurements) / len(self.measurements) if self.measurements else 0

    async def __aenter__(self) -> "MemoryMonitor":
        """Start monitoring memory usage."""
        self.start_memory = self.measure()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Stop monitoring memory usage."""
        self.end_memory = self.measure()

    @property
    def memory_delta(self) -> float:
        """Get memory usage change in MB."""
        return self.end_memory - self.start_memory

    def detect_leaks(self, threshold_mb: float = 1.0) -> Optional[float]:
        """Detect potential memory leaks."""
        if len(self.measurements) < 2:
            return None

        gc.collect()
        gc.collect()

        initial = self.measurements[0]
        final = self.measurements[-1]
        delta = final - initial

        if delta > threshold_mb:
            return delta
        return None


@fixture
async def settings() -> Settings:
    """Create test settings."""
    return Settings(
        batch_size=100,
        max_retries=3,
        retry_delay=0.1,
    )


@fixture
async def document_storage(settings: Settings) -> AsyncGenerator[DocumentStorageService, None]:
    """Create and initialize document storage service."""
    service = DocumentStorageService(
        settings=settings,
        batch_config=BatchConfig(batch_size=10, max_retries=2),
    )
    try:
        yield service
    finally:
        await service.cleanup()


@fixture
async def chunk_storage(settings: Settings) -> AsyncGenerator[ChunkStorageService, None]:
    """Create and initialize chunk storage service."""
    service = ChunkStorageService(
        settings=settings,
        batch_config=BatchConfig(batch_size=10, max_retries=2),
    )
    try:
        yield service
    finally:
        await service.cleanup()


@fixture
async def reference_storage(settings: Settings) -> AsyncGenerator[ReferenceStorageService, None]:
    """Create and initialize reference storage service."""
    service = ReferenceStorageService(
        settings=settings,
        batch_config=BatchConfig(batch_size=10, max_retries=2),
    )
    try:
        yield service
    finally:
        await service.cleanup()


class TestStoragePerformance:
    """Performance benchmarks for storage services."""

    def __init__(self):
        """Initialize test suite."""
        self.reports_dir = Path("test_reports/performance")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.current_report = None

    async def measure_operation_metrics(
        self, operation, operation_name: str, iterations: int = 1
    ) -> Tuple[float, float]:
        """Measure operation execution time and memory usage."""
        metrics = []
        async with MemoryMonitor() as memory:
            start_time = time.perf_counter()
            error = None
            success = True

            try:
                for _ in range(iterations):
                    await operation
                    memory.measure()
            except Exception as e:
                error = str(e)
                success = False

            end_time = time.perf_counter()
            duration = (end_time - start_time) / iterations

            if leak_amount := memory.detect_leaks():
                error = f"Memory leak detected: {leak_amount:.2f} MB"
                success = False

            metrics.append(
                OperationMetrics(
                    operation=operation_name,
                    duration_ms=duration * 1000,
                    memory_mb=memory.memory_delta,
                    throughput=1 / duration if duration > 0 else 0,
                    success=success,
                    error=error,
                )
            )

            if self.current_report:
                self.current_report.operations.extend(metrics)

        return duration, memory.memory_delta

    def start_test_report(self, test_name: str):
        """Start a new test report."""
        self.current_report = TestReport(
            test_name=test_name,
            start_time=time.time(),
            end_time=0,
            total_duration=0,
            operations=[],
            peak_memory_mb=0,
            avg_memory_mb=0,
            total_operations=0,
            successful_operations=0,
            failed_operations=0,
        )

    def finish_test_report(self):
        """Finish and save the current test report."""
        if self.current_report:
            self.current_report.end_time = time.time()
            self.current_report.total_duration = (
                self.current_report.end_time - self.current_report.start_time
            )
            self.current_report.total_operations = len(self.current_report.operations)
            self.current_report.successful_operations = sum(
                1 for op in self.current_report.operations if op.success
            )
            self.current_report.failed_operations = (
                self.current_report.total_operations - self.current_report.successful_operations
            )

            report_path = (
                self.reports_dir / f"{self.current_report.test_name}_{int(time.time())}.json"
            )
            self.current_report.save(report_path)
            self.current_report = None

    @pytest.mark.asyncio
    async def test_memory_leak_detection(
        self,
        document_storage: DocumentStorageService,
        chunk_storage: ChunkStorageService,
        reference_storage: ReferenceStorageService,
    ):
        """Test for memory leaks during repeated operations."""
        async with MemoryMonitor() as memory:
            # Test document operations
            doc = DocumentBuilder().with_title("Test Doc").with_content("Test Content").build()
            for _ in range(10):
                doc_id = await document_storage.store_document(doc)
                await document_storage.get_document(doc_id)
                await document_storage.delete_document(doc_id)
                memory.measure()

            # Test chunk operations
            chunk = (
                ChunkBuilder()
                .with_document_id(UUID(int=1))
                .with_indices(0, 10)
                .with_content("Test Chunk")
                .build()
            )
            for _ in range(10):
                chunk_id = await chunk_storage.store_chunk(chunk)
                await chunk_storage.get_chunk(chunk_id)
                await chunk_storage.delete_chunk(chunk_id)
                memory.measure()

            # Test reference operations
            ref = (
                ReferenceBuilder()
                .with_source(UUID(int=1))
                .with_target(UUID(int=2))
                .with_type("cites")
                .build()
            )
            for _ in range(10):
                await reference_storage.store_reference(ref)
                await reference_storage.get_references(ref.source_id)
                await reference_storage.delete_reference(ref)
                memory.measure()

            # Verify no memory leaks
            leak = memory.detect_leaks(threshold_mb=2.0)
            assert leak is None, f"Memory leak detected across services: {leak:.2f} MB"

    @pytest.mark.asyncio
    async def test_document_batch_throughput(
        self,
        document_storage: DocumentStorageService,
    ):
        """Test document batch operation throughput and memory usage."""
        self.start_test_report("document_batch_throughput")
        try:
            # Create test documents
            num_docs = 100
            docs = [
                DocumentBuilder().with_title(f"Doc {i}").with_content(f"Content {i}").build()
                for i in range(num_docs)
            ]

            # Measure batch store performance with leak detection
            store_time, store_memory = await self.measure_operation_metrics(
                document_storage.batch_store_documents(docs),
                "batch_store_documents",
                iterations=3,  # Multiple iterations to detect leaks
            )
            store_throughput = num_docs / store_time

            # Verify reasonable throughput and memory usage
            assert (
                store_throughput > 10
            ), f"Store throughput too low: {store_throughput:.2f} docs/sec"
            assert store_memory < 100, f"Store memory usage too high: {store_memory:.2f} MB"

            # Get document IDs for cleanup
            doc_ids = [await document_storage.store_document(doc) for doc in docs]

            # Measure batch retrieve performance with leak detection
            retrieve_time, retrieve_memory = await self.measure_operation_metrics(
                document_storage.get_documents(doc_ids), "get_documents", iterations=3
            )
            retrieve_throughput = num_docs / retrieve_time

            # Verify reasonable throughput and memory usage
            assert (
                retrieve_throughput > 20
            ), f"Retrieve throughput too low: {retrieve_throughput:.2f} docs/sec"
            assert retrieve_memory < 50, f"Retrieve memory usage too high: {retrieve_memory:.2f} MB"

            # Cleanup and verify memory is released
            cleanup_time, cleanup_memory = await self.measure_operation_metrics(
                document_storage.delete_documents(doc_ids), "delete_documents"
            )
            assert (
                cleanup_memory < 10
            ), f"Cleanup memory retention too high: {cleanup_memory:.2f} MB"
        finally:
            self.finish_test_report()

    @pytest.mark.asyncio
    async def test_chunk_batch_throughput(
        self,
        chunk_storage: ChunkStorageService,
    ):
        """Test chunk batch operation throughput and memory usage."""
        self.start_test_report("chunk_batch_throughput")
        try:
            # Create test chunks
            num_chunks = 1000
            doc_id = UUID(int=1)
            chunks = [
                ChunkBuilder()
                .with_document_id(doc_id)
                .with_indices(i * 10, (i + 1) * 10)
                .with_content(f"Chunk {i}")
                .build()
                for i in range(num_chunks)
            ]

            # Measure batch store performance
            store_time, store_memory = await self.measure_operation_metrics(
                chunk_storage.batch_store_chunks(chunks), "batch_store_chunks"
            )
            store_throughput = num_chunks / store_time

            # Verify reasonable throughput and memory usage
            assert (
                store_throughput > 100
            ), f"Store throughput too low: {store_throughput:.2f} chunks/sec"
            assert store_memory < 200, f"Store memory usage too high: {store_memory:.2f} MB"

            # Get chunk IDs for cleanup
            chunk_ids = [await chunk_storage.store_chunk(chunk) for chunk in chunks]

            # Measure batch retrieve performance
            retrieve_time, retrieve_memory = await self.measure_operation_metrics(
                chunk_storage.get_chunks(chunk_ids), "get_chunks"
            )
            retrieve_throughput = num_chunks / retrieve_time

            # Verify reasonable throughput and memory usage
            assert (
                retrieve_throughput > 200
            ), f"Retrieve throughput too low: {retrieve_throughput:.2f} chunks/sec"
            assert (
                retrieve_memory < 100
            ), f"Retrieve memory usage too high: {retrieve_memory:.2f} MB"

            # Cleanup and verify memory is released
            cleanup_time, cleanup_memory = await self.measure_operation_metrics(
                chunk_storage.delete_chunks(chunk_ids), "delete_chunks"
            )
            assert (
                cleanup_memory < 20
            ), f"Cleanup memory retention too high: {cleanup_memory:.2f} MB"
        finally:
            self.finish_test_report()

    @pytest.mark.asyncio
    async def test_reference_batch_throughput(
        self,
        reference_storage: ReferenceStorageService,
    ):
        """Test reference batch operation throughput and memory usage."""
        self.start_test_report("reference_batch_throughput")
        try:
            # Create test references
            num_refs = 500
            source_id = UUID(int=1)
            references = [
                ReferenceBuilder()
                .with_source(source_id)
                .with_target(UUID(int=i + 2))
                .with_type("cites")
                .with_confidence(0.8 + (i % 10) * 0.02)
                .build()
                for i in range(num_refs)
            ]

            # Measure batch store performance
            store_time, store_memory = await self.measure_operation_metrics(
                reference_storage.batch_store_references(references), "batch_store_references"
            )
            store_throughput = num_refs / store_time

            # Verify reasonable throughput and memory usage
            assert (
                store_throughput > 50
            ), f"Store throughput too low: {store_throughput:.2f} refs/sec"
            assert store_memory < 150, f"Store memory usage too high: {store_memory:.2f} MB"

            # Measure batch retrieve performance
            retrieve_time, retrieve_memory = await self.measure_operation_metrics(
                reference_storage.get_references(source_id), "get_references"
            )
            retrieve_throughput = num_refs / retrieve_time

            # Verify reasonable throughput and memory usage
            assert (
                retrieve_throughput > 100
            ), f"Retrieve throughput too low: {retrieve_throughput:.2f} refs/sec"
            assert retrieve_memory < 75, f"Retrieve memory usage too high: {retrieve_memory:.2f} MB"

            # Cleanup and verify memory is released
            cleanup_time, cleanup_memory = await self.measure_operation_metrics(
                reference_storage.batch_delete_references(references), "batch_delete_references"
            )
            assert (
                cleanup_memory < 15
            ), f"Cleanup memory retention too high: {cleanup_memory:.2f} MB"
        finally:
            self.finish_test_report()

    @pytest.mark.asyncio
    async def test_concurrent_operations(
        self,
        document_storage: DocumentStorageService,
        chunk_storage: ChunkStorageService,
        reference_storage: ReferenceStorageService,
    ):
        """Test performance and memory usage under concurrent operations."""
        self.start_test_report("concurrent_operations")
        try:
            async with MemoryMonitor() as memory:
                # Create test data
                num_docs = 50
                chunks_per_doc = 20
                refs_per_doc = 10

                docs = [
                    DocumentBuilder().with_title(f"Doc {i}").with_content(f"Content {i}").build()
                    for i in range(num_docs)
                ]

                # Store documents and measure metrics
                doc_store_time, doc_store_memory = await self.measure_operation_metrics(
                    document_storage.batch_store_documents(docs), "batch_store_documents"
                )
                doc_ids = [await document_storage.store_document(doc) for doc in docs]

                # Create and store chunks for each document
                all_chunks = []
                for doc_id in doc_ids:
                    chunks = [
                        ChunkBuilder()
                        .with_document_id(doc_id)
                        .with_indices(i * 10, (i + 1) * 10)
                        .with_content(f"Chunk {i}")
                        .build()
                        for i in range(chunks_per_doc)
                    ]
                    all_chunks.extend(chunks)

                chunk_store_time, chunk_store_memory = await self.measure_operation_metrics(
                    chunk_storage.batch_store_chunks(all_chunks), "batch_store_chunks"
                )

                # Create and store references between documents
                all_refs = []
                for i, source_id in enumerate(doc_ids):
                    refs = [
                        ReferenceBuilder()
                        .with_source(source_id)
                        .with_target(doc_ids[(i + j + 1) % num_docs])
                        .with_type("cites")
                        .with_confidence(0.8 + (j % 10) * 0.02)
                        .build()
                        for j in range(refs_per_doc)
                    ]
                    all_refs.extend(refs)

                ref_store_time, ref_store_memory = await self.measure_operation_metrics(
                    reference_storage.batch_store_references(all_refs), "batch_store_references"
                )

                # Calculate and verify metrics
                total_time = doc_store_time + chunk_store_time + ref_store_time
                total_ops = num_docs + (num_docs * chunks_per_doc) + (num_docs * refs_per_doc)
                throughput = total_ops / total_time
                total_memory = memory.memory_delta

                assert (
                    throughput > 50
                ), f"Concurrent operation throughput too low: {throughput:.2f} ops/sec"
                assert total_memory < 500, f"Total memory usage too high: {total_memory:.2f} MB"

                # Cleanup
                cleanup_time, cleanup_memory = await self.measure_operation_metrics(
                    asyncio.gather(
                        document_storage.delete_documents(doc_ids),
                        chunk_storage.delete_chunks([c.id for c in all_chunks]),
                        reference_storage.batch_delete_references(all_refs),
                    ),
                    "delete_documents",
                )
                assert (
                    cleanup_memory < 50
                ), f"Cleanup memory retention too high: {cleanup_memory:.2f} MB"
        finally:
            self.finish_test_report()
