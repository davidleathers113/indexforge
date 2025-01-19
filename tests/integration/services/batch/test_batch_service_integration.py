"""Integration tests for batch processor service interactions.

Tests the integration between the batch processor and various services,
including Redis caching, Weaviate vector storage, and document storage.
"""

import asyncio
from pathlib import Path
from typing import Dict, List
from uuid import UUID

import pytest

from src.core.metrics import ServiceMetricsCollector
from src.ml.processing.batch.processor import BatchProcessor
from src.ml.processing.document.base import ProcessingResult
from src.services import DocumentStorageService, RedisService, WeaviateClient
from src.services.factory import ServiceFactory

from ..base_tests import BaseServiceTest


class TestBatchServiceIntegration(BaseServiceTest):
    """Test suite for batch processor service integration."""

    @pytest.fixture
    async def batch_processor(self, processor_factory) -> BatchProcessor:
        """Create and initialize batch processor."""
        processor = BatchProcessor(processor_factory.create_word_processor().__class__)
        try:
            yield processor
        finally:
            await processor.cleanup()

    @pytest.mark.asyncio
    async def test_batch_redis_integration(
        self,
        batch_processor: BatchProcessor,
        redis_service: RedisService,
        document_builder,
        tmp_path: Path,
    ):
        """Test batch processor integration with Redis caching."""
        # Create test files
        files = []
        for i in range(5):
            doc_path = document_builder.create_document(
                tmp_path / f"redis_test_{i}.docx",
                paragraphs=[f"Redis test content {i}"],
                tables=[{"rows": 2, "cols": 2, "data": [["A", "B"], ["1", "2"]]}],
            )
            files.append(doc_path)

        # Process batch with Redis caching
        results = await batch_processor.process_batch(files)
        assert len(results) == len(files)
        assert all(result.status == "success" for result in results.values())

        # Verify results are cached in Redis
        for file_path, result in results.items():
            cache_key = f"batch_processor:{file_path}"
            cached_result = await redis_service.get(cache_key)
            assert cached_result is not None
            assert cached_result["status"] == result.status
            assert cached_result["content"] == result.content

    @pytest.mark.asyncio
    async def test_batch_weaviate_integration(
        self,
        batch_processor: BatchProcessor,
        weaviate_service: WeaviateClient,
        document_builder,
        tmp_path: Path,
    ):
        """Test batch processor integration with Weaviate vector storage."""
        # Create test files
        files = []
        for i in range(3):
            doc_path = document_builder.create_document(
                tmp_path / f"weaviate_test_{i}.docx",
                paragraphs=[f"Weaviate test content {i}"],
            )
            files.append(doc_path)

        # Process batch
        results = await batch_processor.process_batch(files)
        assert len(results) == len(files)

        # Store vectors in Weaviate
        vectors = []
        for result in results.values():
            # Extract text content for vector generation
            text = " ".join(paragraph["text"] for paragraph in result.content["text"])
            vector = await weaviate_service.generate_vector(text)
            vectors.append(vector)

        # Add vectors to Weaviate
        uuids = await weaviate_service.batch_add_objects(
            class_name="Document",
            objects=[{"text": str(path)} for path in files],
            vectors=vectors,
        )

        try:
            # Verify vectors are searchable
            query_vector = vectors[0]
            search_results = await weaviate_service.search_vectors(
                class_name="Document",
                vector=query_vector,
                limit=2,
            )
            assert len(search_results) > 0
        finally:
            # Cleanup
            await weaviate_service.delete_batch("Document", uuids)

    @pytest.mark.asyncio
    async def test_batch_storage_integration(
        self,
        batch_processor: BatchProcessor,
        document_storage: DocumentStorageService,
        document_builder,
        tmp_path: Path,
    ):
        """Test batch processor integration with document storage."""
        # Create test files
        files = []
        for i in range(4):
            doc_path = document_builder.create_document(
                tmp_path / f"storage_test_{i}.docx",
                paragraphs=[f"Storage test content {i}"],
            )
            files.append(doc_path)

        # Process batch
        results = await batch_processor.process_batch(files)
        assert len(results) == len(files)

        # Store documents
        doc_ids = []
        for file_path, result in results.items():
            doc_id = await document_storage.store_document(
                {
                    "path": str(file_path),
                    "content": result.content,
                    "metadata": result.metadata,
                }
            )
            doc_ids.append(doc_id)

        try:
            # Verify stored documents
            stored_docs = await document_storage.get_documents(doc_ids)
            assert len(stored_docs) == len(files)
            for doc in stored_docs:
                assert doc is not None
                assert "content" in doc
                assert "metadata" in doc
        finally:
            # Cleanup
            await document_storage.delete_documents(doc_ids)

    @pytest.mark.asyncio
    async def test_concurrent_service_integration(
        self,
        batch_processor: BatchProcessor,
        redis_service: RedisService,
        weaviate_service: WeaviateClient,
        document_storage: DocumentStorageService,
        document_builder,
        tmp_path: Path,
    ):
        """Test concurrent integration with multiple services."""
        # Create test files
        files = []
        for i in range(6):
            doc_path = document_builder.create_document(
                tmp_path / f"concurrent_test_{i}.docx",
                paragraphs=[f"Concurrent test content {i}"],
            )
            files.append(doc_path)

        # Process in two batches concurrently
        batch1 = files[:3]
        batch2 = files[3:]

        results1, results2 = await asyncio.gather(
            batch_processor.process_batch(batch1),
            batch_processor.process_batch(batch2),
        )

        # Verify all results
        assert len(results1) == len(batch1)
        assert len(results2) == len(batch2)

        # Store in services concurrently
        async def store_batch(paths: List[Path], results: Dict[str, ProcessingResult]):
            # Cache in Redis
            cache_tasks = [
                redis_service.set(f"batch_processor:{path}", result.dict())
                for path, result in results.items()
            ]
            await asyncio.gather(*cache_tasks)

            # Store vectors in Weaviate
            vectors = []
            for result in results.values():
                text = " ".join(paragraph["text"] for paragraph in result.content["text"])
                vector = await weaviate_service.generate_vector(text)
                vectors.append(vector)

            uuids = await weaviate_service.batch_add_objects(
                class_name="Document",
                objects=[{"text": str(path)} for path in paths],
                vectors=vectors,
            )

            # Store documents
            doc_ids = []
            for path, result in results.items():
                doc_id = await document_storage.store_document(
                    {
                        "path": str(path),
                        "content": result.content,
                        "metadata": result.metadata,
                    }
                )
                doc_ids.append(doc_id)

            return uuids, doc_ids

        # Store both batches concurrently
        (uuids1, doc_ids1), (uuids2, doc_ids2) = await asyncio.gather(
            store_batch(batch1, results1),
            store_batch(batch2, results2),
        )

        try:
            # Verify storage
            all_doc_ids = doc_ids1 + doc_ids2
            stored_docs = await document_storage.get_documents(all_doc_ids)
            assert len(stored_docs) == len(files)
            assert all(doc is not None for doc in stored_docs)

            # Verify vectors
            all_uuids = uuids1 + uuids2
            for uuid in all_uuids:
                obj = await weaviate_service.get_object("Document", uuid)
                assert obj is not None

        finally:
            # Cleanup
            await asyncio.gather(
                weaviate_service.delete_batch("Document", uuids1),
                weaviate_service.delete_batch("Document", uuids2),
                document_storage.delete_documents(doc_ids1),
                document_storage.delete_documents(doc_ids2),
            )

    @pytest.mark.asyncio
    async def test_service_error_handling(
        self,
        batch_processor: BatchProcessor,
        redis_service: RedisService,
        weaviate_service: WeaviateClient,
        document_storage: DocumentStorageService,
        document_builder,
        tmp_path: Path,
    ):
        """Test error handling during service integration."""
        # Create test files
        valid_file = document_builder.create_document(
            tmp_path / "valid.docx",
            paragraphs=["Valid test content"],
        )
        invalid_file = tmp_path / "invalid.docx"
        invalid_file.write_bytes(b"Invalid content")

        # Process batch with mixed results
        results = await batch_processor.process_batch([valid_file, invalid_file])
        assert len(results) == 2

        # Verify error handling for each service
        valid_result = results[str(valid_file)]
        invalid_result = results[str(invalid_file)]

        # Redis caching with error handling
        await redis_service.set(f"batch_processor:{valid_file}", valid_result.dict())
        await redis_service.set(f"batch_processor:{invalid_file}", invalid_result.dict())

        cached_valid = await redis_service.get(f"batch_processor:{valid_file}")
        cached_invalid = await redis_service.get(f"batch_processor:{invalid_file}")

        assert cached_valid["status"] == "success"
        assert cached_invalid["status"] == "error"

        # Weaviate storage with error handling
        if valid_result.status == "success":
            text = " ".join(paragraph["text"] for paragraph in valid_result.content["text"])
            vector = await weaviate_service.generate_vector(text)
            uuid = await weaviate_service.add_object(
                class_name="Document",
                object_data={"text": str(valid_file)},
                vector=vector,
            )
            try:
                obj = await weaviate_service.get_object("Document", uuid)
                assert obj is not None
            finally:
                await weaviate_service.delete_object("Document", uuid)

        # Document storage with error handling
        if valid_result.status == "success":
            doc_id = await document_storage.store_document(
                {
                    "path": str(valid_file),
                    "content": valid_result.content,
                    "metadata": valid_result.metadata,
                }
            )
            try:
                doc = await document_storage.get_document(doc_id)
                assert doc is not None
            finally:
                await document_storage.delete_document(doc_id)
