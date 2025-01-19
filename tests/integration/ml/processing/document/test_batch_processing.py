"""Integration tests for batch document processing.

Tests the batch processing capabilities of document processors, including
concurrent batch operations, mixed document types, and resource management.
"""

import asyncio
from pathlib import Path
from typing import Dict, List

import pytest

from src.ml.processing.document.base import ProcessingResult

from .base import BaseProcessorTest


class TestBatchProcessing(BaseProcessorTest):
    """Test suite for batch processing functionality."""

    async def _process_batch(self, files: List[Path], processor_factory) -> List[ProcessingResult]:
        """Process a batch of files concurrently."""
        tasks = []
        for file in files:
            if file.suffix == ".docx":
                processor = processor_factory.create_word_processor()
            else:
                processor = processor_factory.create_excel_processor()
            processor.initialize()
            tasks.append(processor.process_async(file))

        try:
            return await asyncio.gather(*tasks)
        finally:
            for task in tasks:
                if hasattr(task, "processor"):
                    task.processor.cleanup()

    @pytest.mark.asyncio
    async def test_batch_processing_integration(
        self, document_builder, excel_builder, processor_factory, tmp_path
    ):
        """Test batch processing integration with different processor types."""
        batch_size = 5
        num_batches = 3
        test_files = []

        # Create test files
        for i in range(batch_size * num_batches):
            # Word files
            doc_path = document_builder.create_document(
                tmp_path / f"batch_test_{i}.docx",
                [f"Batch test content {i}"],
                tables=[{"rows": 2, "cols": 2, "data": [["Table", "Data"]]}],
            )
            test_files.append(doc_path)

            # Excel files
            excel_path = excel_builder.create_workbook(
                tmp_path / f"batch_test_{i}.xlsx",
                {"Sheet1": {"Data": [f"Row {j}" for j in range(10)]}},
            )
            test_files.append(excel_path)

        # Process files in batches
        all_results = []
        for i in range(num_batches):
            start_idx = i * batch_size
            end_idx = start_idx + batch_size
            batch = test_files[start_idx:end_idx]
            results = await self._process_batch(batch, processor_factory)
            all_results.extend(results)

        # Verify results
        assert len(all_results) == batch_size * num_batches
        assert all(result.status == "success" for result in all_results)

        # Verify Word document results
        word_results = [r for r in all_results if "tables" in r.content]
        assert all(len(r.content["tables"]) == 1 for r in word_results)
        assert all("Batch test content" in r.content["text"][0]["text"] for r in word_results)

        # Verify Excel results
        excel_results = [r for r in all_results if "data" in r.content]
        assert all(len(r.content["data"]["Sheet1"]) == 10 for r in excel_results)

    @pytest.mark.asyncio
    async def test_batch_error_handling(
        self, document_builder, excel_builder, processor_factory, tmp_path
    ):
        """Test error handling in batch processing."""
        # Create mix of valid and invalid files
        test_files = []

        # Valid files
        doc_path = document_builder.create_document(tmp_path / "valid.docx", ["Valid document"])
        test_files.append(doc_path)

        excel_path = excel_builder.create_workbook(
            tmp_path / "valid.xlsx", {"Sheet1": {"Data": ["Valid data"]}}
        )
        test_files.append(excel_path)

        # Invalid files
        invalid_doc = tmp_path / "invalid.docx"
        invalid_doc.write_bytes(b"Invalid Word file")
        test_files.append(invalid_doc)

        invalid_excel = tmp_path / "invalid.xlsx"
        invalid_excel.write_bytes(b"Invalid Excel file")
        test_files.append(invalid_excel)

        # Process batch
        results = await self._process_batch(test_files, processor_factory)

        # Verify results
        assert len(results) == 4
        valid_results = [r for r in results if r.status == "success"]
        error_results = [r for r in results if r.status == "error"]

        assert len(valid_results) == 2
        assert len(error_results) == 2
        assert all(len(r.errors) > 0 for r in error_results)

    @pytest.mark.asyncio
    async def test_large_batch_processing(
        self, document_builder, excel_builder, processor_factory, tmp_path
    ):
        """Test processing of large batches of documents."""
        batch_size = 20
        test_files = []

        # Create large batch of test files
        for i in range(batch_size):
            doc_path = document_builder.create_document(
                tmp_path / f"large_batch_{i}.docx", [f"Large batch content {i}"]
            )
            test_files.append(doc_path)

            excel_path = excel_builder.create_workbook(
                tmp_path / f"large_batch_{i}.xlsx",
                {"Sheet1": {"Data": [f"Row {j}" for j in range(5)]}},
            )
            test_files.append(excel_path)

        # Process large batch
        results = await self._process_batch(test_files, processor_factory)

        # Verify results
        assert len(results) == batch_size * 2
        assert all(result.status == "success" for result in results)

        # Verify memory cleanup
        import psutil

        process = psutil.Process()
        memory_info = process.memory_info()
        assert memory_info.rss < 500 * 1024 * 1024  # Less than 500MB
