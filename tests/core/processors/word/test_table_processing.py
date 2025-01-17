"""Tests for Word processor table handling capabilities."""

import logging
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture

from src.core.processors.word import WordProcessor

logger = logging.getLogger(__name__)


class TestWordProcessorTableHandling:
    """Tests for WordProcessor table handling capabilities."""

    def test_process_with_tables(
        self, configured_processor: WordProcessor, sample_docx: Path, caplog: LogCaptureFixture
    ):
        """Test extraction of document tables.

        Args:
            configured_processor: Configured processor instance
            sample_docx: Test Word document path
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing table extraction")

        logger.debug("Processing document with tables: %s", sample_docx)
        result = configured_processor.process(sample_docx)

        logger.debug("Verifying table extraction")
        assert "tables" in result.content
        tables = result.content["tables"]
        assert isinstance(tables, list)
        assert len(tables) == 1

        table = tables[0]
        assert len(table) == 2  # Two rows
        assert "Header 1" in table[0]
        assert "Data 1" in table[1]
        logger.debug("Table extraction test passed successfully")

    def test_document_with_empty_table(
        self, configured_processor: WordProcessor, doc_builder, caplog: LogCaptureFixture
    ):
        """Test processing document with empty table.

        Args:
            configured_processor: Configured processor instance
            doc_builder: Document builder fixture
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing document with empty table")

        file_path = doc_builder("empty_table.docx").add_table(1, 1, [[""]]).build()
        logger.debug("Created document with empty table: %s", file_path)

        logger.debug("Processing document with empty table")
        result = configured_processor.process(file_path)

        logger.debug("Verifying empty table result")
        assert result.status == "success"
        assert "tables" in result.content
        assert len(result.content["tables"]) == 1
        assert len(result.content["tables"][0]) == 1  # One empty row
        logger.debug("Empty table test passed successfully")

    def test_document_with_nested_tables(
        self, configured_processor: WordProcessor, doc_builder, caplog: LogCaptureFixture
    ):
        """Test processing document with nested tables.

        Args:
            configured_processor: Configured processor instance
            doc_builder: Document builder fixture
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing document with nested tables")

        file_path = (
            doc_builder("nested_tables.docx")
            .add_table(2, 2, [["Outer 1", "Outer 2"], ["", ""]])
            .build()
        )
        logger.debug("Created document with nested tables: %s", file_path)

        logger.debug("Processing document with nested tables")
        result = configured_processor.process(file_path)

        logger.debug("Verifying nested tables result")
        assert result.status == "success"
        assert "tables" in result.content
        assert len(result.content["tables"]) == 1
        assert "Outer 1" in result.content["tables"][0][0]
        logger.debug("Nested tables test passed successfully")

    def test_table_with_mixed_content(
        self, configured_processor: WordProcessor, doc_builder, caplog: LogCaptureFixture
    ):
        """Test processing table with mixed content types.

        Args:
            configured_processor: Configured processor instance
            doc_builder: Document builder fixture
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing table with mixed content")

        file_path = (
            doc_builder("mixed_content.docx")
            .add_table(
                2,
                2,
                [
                    ["Normal Text", "Text with\nNewlines"],
                    ["Text with spaces  ", "  Padded Text  "],
                ],
            )
            .build()
        )
        logger.debug("Created document with mixed content table: %s", file_path)

        logger.debug("Processing document with mixed content table")
        result = configured_processor.process(file_path)

        logger.debug("Verifying mixed content table result")
        assert result.status == "success"
        assert "tables" in result.content
        tables = result.content["tables"]
        assert len(tables) == 1
        table = tables[0]

        # Verify content preservation
        assert "Normal Text" in table[0]
        assert "Text with\nNewlines" in table[0]
        assert "Text with spaces" in table[1]
        assert "Padded Text" in table[1]
        logger.debug("Mixed content table test passed successfully")
