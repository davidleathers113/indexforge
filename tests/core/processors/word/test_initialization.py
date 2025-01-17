"""Tests for Word processor initialization and configuration."""

import logging
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture

from src.core.processors.word import WordProcessor

logger = logging.getLogger(__name__)


class TestWordProcessorInitialization:
    """Tests for WordProcessor initialization and configuration."""

    def test_initialization_default(self, word_processor: WordProcessor, caplog: LogCaptureFixture):
        """Test processor initialization with default settings.

        Args:
            word_processor: Default processor instance
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing default WordProcessor initialization")

        logger.debug("Verifying default settings")
        assert not word_processor.extract_headers
        assert not word_processor.extract_tables
        assert not word_processor.extract_images
        logger.debug("Default settings verified successfully")

    def test_initialization_configured(
        self, configured_processor: WordProcessor, caplog: LogCaptureFixture
    ):
        """Test processor initialization with custom configuration.

        Args:
            configured_processor: Configured processor instance
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing configured WordProcessor initialization")

        logger.debug("Verifying configured settings")
        assert configured_processor.extract_headers
        assert configured_processor.extract_tables
        assert configured_processor.extract_images
        logger.debug("Configured settings verified successfully")

    def test_invalid_configuration(self, caplog: LogCaptureFixture):
        """Test processor initialization with invalid configuration.

        Args:
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing invalid configuration handling")

        invalid_config = {"extract_headers": "invalid", "extract_tables": None}
        logger.debug("Creating processor with invalid config: %s", invalid_config)

        with pytest.raises(ValueError) as exc_info:
            WordProcessor(invalid_config)

        logger.debug("Verifying error message: %s", exc_info.value)
        assert "Invalid configuration" in str(exc_info.value)
