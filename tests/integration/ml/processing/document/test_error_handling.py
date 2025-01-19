"""Tests for document processing error handling.

This module contains integration tests for error handling scenarios in document
processing, including invalid files, resource cleanup, and error recovery.
"""

import logging
from pathlib import Path

import pytest

from src.ml.processing.document.base import ProcessingError, ProcessingResult

from .base_tests import BaseProcessorTest


class TestErrorHandling(BaseProcessorTest):
    """Test suite for document processing error handling."""

    def test_invalid_word_file(self, tmp_path, processor_factory, caplog):
        """Test processing of an invalid Word file."""
        caplog.set_level(logging.ERROR)

        # Create invalid file
        invalid_path = tmp_path / "invalid.docx"
        invalid_path.write_bytes(b"Not a valid Word file")

        # Process invalid file
        processor = processor_factory.create_word_processor()
        processor.initialize()
        result = processor.process(invalid_path)
        processor.cleanup()

        # Verify error handling
        self.verify_error_processing(result)
        assert any("Failed to process Word document" in record.message for record in caplog.records)

    def test_invalid_excel_file(self, tmp_path, processor_factory, caplog):
        """Test processing of an invalid Excel file."""
        caplog.set_level(logging.ERROR)

        # Create invalid file
        invalid_path = tmp_path / "invalid.xlsx"
        invalid_path.write_bytes(b"Not a valid Excel file")

        # Process invalid file
        processor = processor_factory.create_excel_processor()
        processor.initialize()
        result = processor.process(invalid_path)
        processor.cleanup()

        # Verify error handling
        self.verify_error_processing(result)
        assert any("Failed to process Excel file" in record.message for record in caplog.records)

    def test_cleanup_after_error(self, tmp_path, processor_factory):
        """Test resource cleanup after processing errors."""
        # Create invalid file
        invalid_path = tmp_path / "invalid.docx"
        invalid_path.write_bytes(b"Invalid content")

        # Process with error
        processor = processor_factory.create_word_processor()
        processor.initialize()
        result = processor.process(invalid_path)
        processor.cleanup()

        # Verify cleanup
        self.verify_error_processing(result)
        self.verify_resource_cleanup(processor)

        # Verify processor cannot be used after cleanup
        with pytest.raises(RuntimeError):
            processor.process(invalid_path)

    @pytest.mark.asyncio
    async def test_async_error_handling(self, tmp_path, processor_factory):
        """Test error handling in async processing."""
        # Create invalid file
        invalid_path = tmp_path / "invalid.docx"
        invalid_path.write_bytes(b"Invalid content")

        # Process with error
        processor = processor_factory.create_word_processor()
        processor.initialize()

        with pytest.raises(ProcessingError):
            await processor.process_async(invalid_path)

        processor.cleanup()
        self.verify_resource_cleanup(processor)

    def test_mixed_success_and_error(self, document_builder, tmp_path, processor_factory):
        """Test handling of mixed successful and failed processing."""
        # Create valid and invalid files
        valid_path = document_builder.with_paragraph("Valid content").build("valid.docx")
        invalid_path = tmp_path / "invalid.docx"
        invalid_path.write_bytes(b"Invalid content")

        # Process both files
        processor = processor_factory.create_word_processor()
        processor.initialize()

        valid_result = processor.process(valid_path)
        invalid_result = processor.process(invalid_path)

        processor.cleanup()

        # Verify results
        self.verify_successful_processing(valid_result)
        self.verify_error_processing(invalid_result)
        self.verify_resource_cleanup(processor)
