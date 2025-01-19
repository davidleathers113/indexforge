"""Tests for Word processor content extraction capabilities."""

import logging
from pathlib import Path

from _pytest.logging import LogCaptureFixture

from src.core.processors.word import WordProcessor


logger = logging.getLogger(__name__)


class TestWordProcessorContentExtraction:
    """Tests for WordProcessor content extraction capabilities."""

    def test_process_docx_success(
        self, configured_processor: WordProcessor, sample_docx: Path, caplog: LogCaptureFixture
    ):
        """Test successful processing of Word document.

        Args:
            configured_processor: Configured processor instance
            sample_docx: Test Word document path
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing successful Word document processing")

        logger.debug("Processing Word document: %s", sample_docx)
        result = configured_processor.process(sample_docx)

        logger.debug("Verifying processing result")
        assert result.status == "success"
        assert "content" in result.content
        assert "metadata" in result.content
        assert "First paragraph" in result.content["content"]
        assert "Second paragraph" in result.content["content"]

        if configured_processor.extract_headers:
            logger.debug("Verifying headers extraction")
            assert "headers" in result.content
            headers = result.content["headers"]
            assert isinstance(headers, dict)
            assert "level_1" in headers
            assert "level_2" in headers
            assert "level_3" in headers
            assert "Heading 1" in headers["level_1"]
            assert "Heading 2" in headers["level_2"]
            assert "Heading 3" in headers["level_3"]

        logger.debug("Content processing test passed successfully")

    def test_selective_extraction(self, doc_builder, caplog: LogCaptureFixture):
        """Test selective content extraction based on configuration.

        Args:
            doc_builder: Document builder fixture
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing selective content extraction")

        config = {"extract_headers": True, "extract_tables": False, "extract_images": False}
        logger.debug("Creating processor with selective extraction: %s", config)
        processor = WordProcessor(config)

        file_path = (
            doc_builder("test.docx")
            .add_headers({1: "Test Heading"})
            .add_table(1, 1, [["Test Data"]])
            .build()
        )

        logger.debug("Processing file with selective extraction")
        result = processor.process(file_path)

        logger.debug("Verifying selective extraction")
        assert "headers" in result.content
        assert "tables" not in result.content
        assert "images" not in result.content
        logger.debug("Selective extraction test passed successfully")
