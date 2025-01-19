"""Integration tests for mixed content document processing.

Tests the processing of documents containing mixed content types, including
tables, text, multiple sheets, and various data formats.
"""

from pathlib import Path

import pytest

from src.ml.processing.document.base import ProcessingResult

from .base import BaseProcessorTest


class TestMixedContentProcessing(BaseProcessorTest):
    """Test suite for processing documents with mixed content types."""

    def test_word_mixed_content(self, document_builder, processor_factory, tmp_path):
        """Test processing Word documents with mixed content types."""
        # Create Word document with various content types
        doc_path = document_builder.create_document(
            tmp_path / "mixed_word.docx",
            paragraphs=["Mixed content test", "Another paragraph"],
            tables=[
                {"rows": 2, "cols": 2, "data": [["Header 1", "Header 2"], ["Data 1", "Data 2"]]},
                {"rows": 3, "cols": 1, "data": [["List Item 1"], ["List Item 2"], ["List Item 3"]]},
            ],
            headers=["Section 1", "Section 2"],
        )

        # Process document
        processor = processor_factory.create_word_processor()
        processor.initialize()
        try:
            result = processor.process(doc_path)

            # Verify mixed content handling
            assert result.status == "success"
            assert len(result.content["text"]) == 4  # 2 paragraphs + 2 headers
            assert len(result.content["tables"]) == 2
            assert result.content["tables"][0]["rows"] == 2
            assert result.content["tables"][1]["rows"] == 3
            assert "Mixed content test" in result.content["text"][0]["text"]
            assert "Section" in result.content["text"][2]["text"]
        finally:
            processor.cleanup()

    def test_excel_mixed_content(self, excel_builder, processor_factory, tmp_path):
        """Test processing Excel files with mixed content types."""
        # Create Excel file with multiple sheets and data types
        excel_path = excel_builder.create_workbook(
            tmp_path / "mixed_excel.xlsx",
            sheets={
                "Numeric": {"Values": [1, 2, 3, 4, 5]},
                "Text": {"Names": ["Alice", "Bob", "Charlie"]},
                "Mixed": {"ID": [1, 2, 3], "Name": ["X", "Y", "Z"], "Score": [95.5, 87.3, 92.1]},
            },
        )

        # Process workbook
        processor = processor_factory.create_excel_processor()
        processor.initialize()
        try:
            result = processor.process(excel_path)

            # Verify mixed content handling
            assert result.status == "success"
            assert len(result.content["data"]) == 3  # Three sheets
            assert len(result.content["data"]["Numeric"]) == 5
            assert len(result.content["data"]["Text"]) == 3
            assert len(result.content["data"]["Mixed"].columns) == 3
            assert "Score" in result.content["data"]["Mixed"].columns
        finally:
            processor.cleanup()

    def test_cross_format_validation(
        self, document_builder, excel_builder, processor_factory, tmp_path
    ):
        """Test processing and validating content across different formats."""
        # Create documents with related content
        table_data = [
            ["Product", "Price", "Quantity"],
            ["A", "10.0", "100"],
            ["B", "20.0", "200"],
            ["C", "30.0", "300"],
        ]

        # Create Word document with table
        doc_path = document_builder.create_document(
            tmp_path / "inventory.docx",
            paragraphs=["Inventory Report"],
            tables=[{"rows": 4, "cols": 3, "data": table_data}],
        )

        # Create Excel with same data
        excel_path = excel_builder.create_workbook(
            tmp_path / "inventory.xlsx",
            sheets={
                "Inventory": {
                    "Product": ["A", "B", "C"],
                    "Price": [10.0, 20.0, 30.0],
                    "Quantity": [100, 200, 300],
                }
            },
        )

        # Process both documents
        word_processor = processor_factory.create_word_processor()
        excel_processor = processor_factory.create_excel_processor()

        try:
            word_processor.initialize()
            excel_processor.initialize()

            word_result = word_processor.process(doc_path)
            excel_result = excel_processor.process(excel_path)

            # Verify cross-format content matching
            assert word_result.status == "success"
            assert excel_result.status == "success"

            # Extract data for comparison
            word_table = word_result.content["tables"][0]
            excel_data = excel_result.content["data"]["Inventory"]

            # Compare content
            assert len(word_table["data"]) == len(excel_data) + 1  # +1 for header row
            for i, row in enumerate(word_table["data"][1:]):  # Skip header row
                assert float(row[1]) == excel_data["Price"][i]  # Compare prices
                assert int(row[2]) == excel_data["Quantity"][i]  # Compare quantities
        finally:
            word_processor.cleanup()
            excel_processor.cleanup()

    def test_complex_document_structure(self, document_builder, processor_factory, tmp_path):
        """Test processing documents with complex nested structures."""
        # Create document with nested tables and mixed content
        doc_path = document_builder.create_document(
            tmp_path / "complex.docx",
            paragraphs=["Executive Summary", "This document contains complex nested structures."],
            tables=[
                {
                    "rows": 3,
                    "cols": 3,
                    "data": [
                        ["Region", "Q1", "Q2"],
                        ["North", "100", "150"],
                        ["South", "120", "180"],
                    ],
                },
                {"rows": 2, "cols": 2, "data": [["Category", "Count"], ["Total", "550"]]},
            ],
            headers=["Financial Report", "Regional Breakdown", "Summary"],
        )

        # Process document
        processor = processor_factory.create_word_processor()
        processor.initialize()
        try:
            result = processor.process(doc_path)

            # Verify complex structure handling
            assert result.status == "success"
            assert len(result.content["text"]) > 4  # Multiple text elements
            assert len(result.content["tables"]) == 2

            # Verify nested structure preservation
            main_table = result.content["tables"][0]
            summary_table = result.content["tables"][1]

            assert main_table["cols"] == 3
            assert main_table["rows"] == 3
            assert summary_table["cols"] == 2
            assert summary_table["rows"] == 2

            # Verify content relationships
            assert any("Executive Summary" in text["text"] for text in result.content["text"])
            assert any("Financial Report" in text["text"] for text in result.content["text"])
            assert main_table["data"][0][0] == "Region"
            assert summary_table["data"][0][0] == "Category"
        finally:
            processor.cleanup()
