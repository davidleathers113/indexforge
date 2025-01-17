"""Tests for Word processor file handling capabilities."""

import logging
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture

from src.core.processors.word import WordProcessor

logger = logging.getLogger(__name__)


class TestWordProcessorFileHandling:
    """Tests for WordProcessor file handling capabilities."""

    def test_can_process_docx(
        self, word_processor: WordProcessor, tmp_path: Path, caplog: LogCaptureFixture
    ):
        """Test file type detection for Word documents.

        Args:
            word_processor: Default processor instance
            tmp_path: Temporary directory path
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing Word document type detection")

        file_path = tmp_path / "test.docx"
        logger.debug("Testing file path: %s", file_path)
        assert word_processor.can_process(file_path)
        logger.debug("Word document type detection test passed")

    def test_can_process_unsupported(
        self, word_processor: WordProcessor, tmp_path: Path, caplog: LogCaptureFixture
    ):
        """Test file type detection for unsupported files.

        Args:
            word_processor: Default processor instance
            tmp_path: Temporary directory path
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing unsupported file type detection")

        for ext in [".doc", ".txt", ".pdf"]:
            file_path = tmp_path / f"test{ext}"
            logger.debug("Testing unsupported extension: %s with path: %s", ext, file_path)
            assert not word_processor.can_process(file_path)
        logger.debug("Unsupported file type detection test passed")

    def test_process_invalid_file(
        self, word_processor: WordProcessor, tmp_path: Path, caplog: LogCaptureFixture
    ):
        """Test processing invalid file.

        Args:
            word_processor: Default processor instance
            tmp_path: Temporary directory path
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing invalid file processing")

        file_path = tmp_path / "invalid.docx"
        logger.debug("Creating invalid Word document: %s", file_path)
        file_path.write_text("Invalid content")

        logger.debug("Processing invalid file")
        result = word_processor.process(file_path)

        logger.debug("Verifying error result")
        assert result.status == "error"
        assert result.error is not None
        logger.debug("Invalid file test passed successfully")

    def test_empty_document(
        self, word_processor: WordProcessor, doc_builder, caplog: LogCaptureFixture
    ):
        """Test processing empty document.

        Args:
            word_processor: Default processor instance
            doc_builder: Document builder fixture
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing empty document processing")

        file_path = doc_builder("empty.docx").build()
        logger.debug("Created empty Word document: %s", file_path)

        logger.debug("Processing empty document")
        result = word_processor.process(file_path)

        logger.debug("Verifying empty document result")
        assert result.status == "success"
        assert result.content["content"] == ""
        logger.debug("Empty document test passed successfully")
