"""Tests for sequential document processing scenarios.

This module contains integration tests for sequential processing of documents,
focusing on basic functionality and proper resource management.
"""

import logging
from pathlib import Path
from typing import Dict

import pytest

from src.ml.processing.document.base import ProcessingResult

from .base_tests import BaseProcessorTest
from .builders import DocumentBuilder, ExcelBuilder


class TestSequentialProcessing(BaseProcessorTest):
    """Test suite for sequential document processing."""

    def test_basic_word_processing(self, document_builder, processor_factory, caplog):
        """Test basic Word document processing functionality."""
        caplog.set_level(logging.INFO)

        # Create test document
        doc_path = (
            document_builder.with_paragraph("Test content from Word")
            .with_table(2, 2, "Word table content")
            .build("test.docx")
        )

        # Process document
        processor = processor_factory.create_word_processor()
        processor.initialize()
        result = processor.process(doc_path)
        processor.cleanup()

        # Verify results
        self.verify_successful_processing(result)
        assert "Test content from Word" in result.content["text"][0]["text"]
        assert len(result.content["tables"]) == 1
        assert any("Word processor initialized" in record.message for record in caplog.records)

    def test_basic_excel_processing(self, excel_builder, processor_factory, caplog):
        """Test basic Excel file processing functionality."""
        caplog.set_level(logging.INFO)

        # Create test file
        excel_path = excel_builder.with_sheet("Sheet1", {"A": [1, 2], "B": ["x", "y"]}).build(
            "test.xlsx"
        )

        # Process file
        processor = processor_factory.create_excel_processor()
        processor.initialize()
        result = processor.process(excel_path)
        processor.cleanup()

        # Verify results
        self.verify_successful_processing(result)
        assert len(result.content["data"]) == 1  # One sheet
        assert list(result.content["data"]["Sheet1"].columns) == ["A", "B"]
        assert any("Excel processor initialized" in record.message for record in caplog.records)

    @pytest.mark.parametrize(
        "proc_type,content",
        [
            ("word", "Test Word content"),
            ("excel", {"A": [1, 2, 3]}),
        ],
    )
    def test_processor_lifecycle(self, tmp_path, processor_factory, proc_type, content, caplog):
        """Test processor lifecycle including initialization and cleanup.

        Args:
            proc_type: Type of processor to test
            content: Content to process
        """
        caplog.set_level(logging.INFO)

        # Create test file
        if proc_type == "word":
            path = DocumentBuilder(tmp_path).with_paragraph(content).build("test.docx")
            processor = processor_factory.create_word_processor()
        else:
            path = ExcelBuilder(tmp_path).with_sheet("Sheet1", content).build("test.xlsx")
            processor = processor_factory.create_excel_processor()

        # Test lifecycle
        processor.initialize()
        result = processor.process(path)
        processor.cleanup()

        # Verify
        self.verify_successful_processing(result)
        self.verify_resource_cleanup(processor)
        assert any(
            f"{proc_type.capitalize()} processor cleaned up" in record.message
            for record in caplog.records
        )
