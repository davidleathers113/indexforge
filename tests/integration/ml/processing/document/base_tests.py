"""Base classes for processor integration tests.

This module provides base test classes with common utilities and fixtures
for processor integration testing.
"""

from pathlib import Path

import pytest

from src.ml.processing.document.base import ProcessingResult

from .builders import DocumentBuilder, ExcelBuilder
from .factories import ProcessorTestFactory


class BaseProcessorTest:
    """Base class for processor tests with common utilities."""

    @pytest.fixture
    def document_builder(self, tmp_path) -> DocumentBuilder:
        """Fixture providing a document builder.

        Args:
            tmp_path: pytest temporary directory fixture

        Returns:
            Configured DocumentBuilder instance
        """
        return DocumentBuilder(tmp_path)

    @pytest.fixture
    def excel_builder(self, tmp_path) -> ExcelBuilder:
        """Fixture providing an Excel builder.

        Args:
            tmp_path: pytest temporary directory fixture

        Returns:
            Configured ExcelBuilder instance
        """
        return ExcelBuilder(tmp_path)

    @pytest.fixture
    def processor_factory(self) -> ProcessorTestFactory:
        """Fixture providing a processor factory.

        Returns:
            ProcessorTestFactory instance
        """
        return ProcessorTestFactory()

    def verify_successful_processing(self, result: ProcessingResult) -> None:
        """Verify successful processing result.

        Args:
            result: Processing result to verify

        Raises:
            AssertionError: If verification fails
        """
        assert result.status == "success", f"Processing failed with status: {result.status}"
        assert result.content, "No content in processing result"
        assert not result.errors, f"Unexpected errors: {result.errors}"

    def verify_error_processing(self, result: ProcessingResult) -> None:
        """Verify error processing result.

        Args:
            result: Processing result to verify

        Raises:
            AssertionError: If verification fails
        """
        assert result.status == "error", f"Expected error status but got: {result.status}"
        assert result.errors, "No errors in error result"

    def verify_resource_cleanup(self, processor) -> None:
        """Verify processor resources are cleaned up.

        Args:
            processor: Processor instance to verify

        Raises:
            AssertionError: If verification fails
        """
        assert not processor.is_initialized, "Processor still initialized after cleanup"
