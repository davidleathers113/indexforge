"""Tests for document processor resource management.

This module contains integration tests for resource management in document
processing, including initialization, cleanup, and context manager usage.
"""

import asyncio
import logging
from pathlib import Path
from typing import AsyncIterator

import pytest

from src.ml.processing.document.base import ProcessingResult

from .base_tests import BaseProcessorTest


class TestResourceManagement(BaseProcessorTest):
    """Test suite for document processor resource management."""

    async def _process_with_context(
        self, processor, file_path: Path
    ) -> AsyncIterator[ProcessingResult]:
        """Process a file using the processor's context manager.

        Args:
            processor: Document processor instance
            file_path: Path to file to process

        Yields:
            Processing results
        """
        async with processor:
            result = await processor.process_async(file_path)
            yield result

    def test_processor_lifecycle(self, document_builder, processor_factory, caplog):
        """Test complete processor lifecycle."""
        caplog.set_level(logging.INFO)

        # Create test document
        doc_path = document_builder.with_paragraph("Lifecycle test").build("test.docx")

        # Test initialization
        processor = processor_factory.create_word_processor()
        assert not processor.is_initialized

        processor.initialize()
        assert processor.is_initialized
        assert any("processor initialized" in record.message for record in caplog.records)

        # Process document
        result = processor.process(doc_path)
        self.verify_successful_processing(result)

        # Test cleanup
        processor.cleanup()
        self.verify_resource_cleanup(processor)
        assert any("processor cleaned up" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_context_manager(self, document_builder, processor_factory):
        """Test processor context manager functionality."""
        # Create test document
        doc_path = document_builder.with_paragraph("Context test").build("test.docx")

        # Process using context manager
        processor = processor_factory.create_word_processor()
        async with processor:
            assert processor.is_initialized
            result = await processor.process_async(doc_path)
            self.verify_successful_processing(result)

        # Verify cleanup after context
        self.verify_resource_cleanup(processor)

    @pytest.mark.asyncio
    async def test_concurrent_resource_management(self, document_builder, processor_factory):
        """Test resource management with concurrent processing."""
        # Create test documents
        docs = [
            document_builder.with_paragraph(f"Doc {i}").build(f"test_{i}.docx") for i in range(3)
        ]

        # Process concurrently using context managers
        processor = processor_factory.create_word_processor()
        tasks = [self._process_with_context(processor, doc) for doc in docs]

        results = []
        for task in asyncio.as_completed(tasks):
            async for result in await task:
                results.append(result)
                self.verify_successful_processing(result)

        # Verify final cleanup
        self.verify_resource_cleanup(processor)

    def test_cleanup_after_exception(self, processor_factory):
        """Test resource cleanup after processing exceptions."""
        # Test cleanup after exception
        processor = processor_factory.create_word_processor()
        processor.initialize()

        try:
            # Simulate processing error
            raise RuntimeError("Simulated processing error")
        except RuntimeError:
            processor.cleanup()

        # Verify cleanup occurred
        self.verify_resource_cleanup(processor)

    @pytest.mark.asyncio
    async def test_resource_limits(self, document_builder, processor_factory):
        """Test processor behavior under resource constraints."""
        # Create multiple test documents
        docs = [
            document_builder.with_paragraph("Resource test").build(f"test_{i}.docx")
            for i in range(5)
        ]

        # Process documents with resource limits
        processor = processor_factory.create_word_processor()
        async with processor:
            # Process in smaller batches to manage resources
            batch_size = 2
            for i in range(0, len(docs), batch_size):
                batch = docs[i : i + batch_size]
                tasks = [processor.process_async(doc) for doc in batch]
                results = await asyncio.gather(*tasks)

                for result in results:
                    self.verify_successful_processing(result)
                    assert result.resources_released

        # Verify final cleanup
        self.verify_resource_cleanup(processor)
