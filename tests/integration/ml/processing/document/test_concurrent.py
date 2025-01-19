"""Tests for concurrent document processing scenarios.

This module contains integration tests for concurrent processing of documents,
focusing on parallel execution and resource management.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List

import pytest

from src.ml.processing.document.base import ProcessingResult

from .base_tests import BaseProcessorTest
from .builders import DocumentBuilder, ExcelBuilder


class TestConcurrentProcessing(BaseProcessorTest):
    """Test suite for concurrent document processing."""

    async def _process_files(self, processor, files: List[Path]) -> List[ProcessingResult]:
        """Process multiple files concurrently.

        Args:
            processor: Document processor instance
            files: List of files to process

        Returns:
            List of processing results
        """
        processor.initialize()
        try:
            tasks = [processor.process_async(file) for file in files]
            return await asyncio.gather(*tasks)
        finally:
            processor.cleanup()

    @pytest.mark.asyncio
    async def test_concurrent_word_processing(self, document_builder, processor_factory):
        """Test concurrent processing of Word documents."""
        # Create test files
        files = []
        for i in range(3):
            path = (
                document_builder.with_paragraph(f"Content {i}")
                .with_table(2, 2, f"Table {i}")
                .build(f"doc_{i}.docx")
            )
            files.append(path)

        # Process concurrently
        processor = processor_factory.create_word_processor()
        results = await self._process_files(processor, files)

        # Verify results
        assert len(results) == len(files)
        for i, result in enumerate(results):
            self.verify_successful_processing(result)
            assert f"Content {i}" in result.content["text"][0]["text"]
            assert len(result.content["tables"]) == 1

    @pytest.mark.asyncio
    async def test_concurrent_excel_processing(self, excel_builder, processor_factory):
        """Test concurrent processing of Excel files."""
        # Create test files
        files = []
        for i in range(3):
            path = excel_builder.with_sheet(
                "Sheet1",
                {"Value": range(i, i + 3)},
            ).build(f"excel_{i}.xlsx")
            files.append(path)

        # Process concurrently
        processor = processor_factory.create_excel_processor()
        results = await self._process_files(processor, files)

        # Verify results
        assert len(results) == len(files)
        for result in results:
            self.verify_successful_processing(result)
            assert len(result.content["data"]) == 1  # One sheet
            assert "Value" in result.content["data"]["Sheet1"].columns

    @pytest.mark.asyncio
    async def test_mixed_concurrent_processing(
        self, document_builder, excel_builder, processor_factory
    ):
        """Test concurrent processing of mixed document types."""
        # Create test files
        word_files = [document_builder.with_paragraph("Word content").build("doc.docx")]
        excel_files = [excel_builder.with_sheet("Sheet1", {"A": [1, 2]}).build("excel.xlsx")]

        # Process each type concurrently
        word_processor = processor_factory.create_word_processor()
        excel_processor = processor_factory.create_excel_processor()

        # Run both processors concurrently
        word_task = self._process_files(word_processor, word_files)
        excel_task = self._process_files(excel_processor, excel_files)
        word_results, excel_results = await asyncio.gather(word_task, excel_task)

        # Verify Word results
        assert len(word_results) == len(word_files)
        for result in word_results:
            self.verify_successful_processing(result)
            assert "Word content" in result.content["text"][0]["text"]

        # Verify Excel results
        assert len(excel_results) == len(excel_files)
        for result in excel_results:
            self.verify_successful_processing(result)
            assert "A" in result.content["data"]["Sheet1"].columns
