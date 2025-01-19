"""Tests for the base document processor functionality.

This module contains tests for the BaseProcessor class and ProcessingResult,
establishing common test cases that will be inherited by specific processor tests.
"""

import logging
from pathlib import Path
from typing import Any

from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture
import pytest

from src.core.processors.base import BaseProcessor, ProcessingResult


# Configure logging for tests
logger = logging.getLogger(__name__)


class TestProcessor(BaseProcessor):
    """Test implementation of BaseProcessor for testing."""

    def __init__(
        self, config: dict[str, Any] | None = None, supported_extensions: set[str] = None
    ):
        """Initialize test processor with optional configuration and supported extensions.

        Args:
            config: Optional configuration dictionary
            supported_extensions: Set of supported file extensions
        """
        logger.debug(
            "Initializing TestProcessor with config=%s, supported_extensions=%s",
            config,
            supported_extensions,
        )
        super().__init__(config)
        self.supported_extensions = supported_extensions or {".test"}

    def can_process(self, file_path: Path) -> bool:
        """Check if file can be processed based on extension.

        Args:
            file_path: Path to check

        Returns:
            bool: True if extension is supported
        """
        result = file_path.suffix.lower() in self.supported_extensions
        logger.debug(
            "Checking if %s can be processed: %s (supported: %s)",
            file_path,
            result,
            self.supported_extensions,
        )
        return result


@pytest.fixture
def test_processor(request: FixtureRequest, caplog: LogCaptureFixture):
    """Fixture providing a test processor instance.

    Args:
        request: Pytest request object for test context
        caplog: Fixture for capturing log messages

    Returns:
        TestProcessor: Configured test processor instance
    """
    caplog.set_level(logging.DEBUG)
    logger.info("Creating test processor for test: %s", request.node.name)
    processor = TestProcessor()
    yield processor
    logger.info("Cleaning up test processor for test: %s", request.node.name)


@pytest.fixture
def test_file(tmp_path: Path, request: FixtureRequest):
    """Fixture providing a test file path.

    Args:
        tmp_path: Pytest fixture providing temporary directory
        request: Pytest request object for test context

    Returns:
        Path: Path to test file
    """
    logger.info("Creating test file for test: %s", request.node.name)
    file_path = tmp_path / "test.test"
    file_path.touch()
    logger.debug("Created test file at: %s", file_path)
    return file_path


class TestProcessingResult:
    """Tests for the ProcessingResult class."""

    def test_success_creation(self, caplog: LogCaptureFixture):
        """Test creating a successful processing result.

        Args:
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing successful ProcessingResult creation")

        content = {"key": "value"}
        logger.debug("Creating success result with content: %s", content)
        result = ProcessingResult.success(content)

        logger.debug(
            "Verifying result attributes: status=%s, content=%s, error=%s",
            result.status,
            result.content,
            result.error,
        )
        assert result.status == "success"
        assert result.content == content
        assert result.error is None

    def test_error_creation(self, caplog: LogCaptureFixture):
        """Test creating an error processing result.

        Args:
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing error ProcessingResult creation")

        error_msg = "Test error"
        partial_content = {"partial": "data"}
        logger.debug(
            "Creating error result with message: %s, content: %s", error_msg, partial_content
        )
        result = ProcessingResult.create_error(error_msg, partial_content)

        logger.debug(
            "Verifying result attributes: status=%s, content=%s, error=%s",
            result.status,
            result.content,
            result.error,
        )
        assert result.status == "error"
        assert result.content == partial_content
        assert result.error == error_msg

    def test_error_creation_without_content(self, caplog: LogCaptureFixture):
        """Test creating an error result without partial content.

        Args:
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing error ProcessingResult creation without content")

        error_msg = "Test error"
        logger.debug("Creating error result with message: %s", error_msg)
        result = ProcessingResult.create_error(error_msg)

        logger.debug(
            "Verifying result attributes: status=%s, content=%s, error=%s",
            result.status,
            result.content,
            result.error,
        )
        assert result.status == "error"
        assert result.content == {}
        assert result.error == error_msg


class TestBaseProcessor:
    """Tests for the BaseProcessor class."""

    def test_initialization_with_config(self, caplog: LogCaptureFixture):
        """Test processor initialization with configuration.

        Args:
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing BaseProcessor initialization with config")

        config = {"key": "value"}
        logger.debug("Creating processor with config: %s", config)
        processor = TestProcessor(config)

        logger.debug("Verifying processor config: %s", processor.config)
        assert processor.config == config

    def test_initialization_without_config(self, caplog: LogCaptureFixture):
        """Test processor initialization without configuration.

        Args:
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing BaseProcessor initialization without config")

        logger.debug("Creating processor with no config")
        processor = TestProcessor()

        logger.debug("Verifying processor has empty config: %s", processor.config)
        assert processor.config == {}

    def test_can_process_supported_extension(
        self, test_processor: TestProcessor, tmp_path: Path, caplog: LogCaptureFixture
    ):
        """Test can_process with supported file extension.

        Args:
            test_processor: Test processor instance
            tmp_path: Temporary directory path
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing can_process with supported extension")

        file_path = tmp_path / "test.test"
        logger.debug("Testing file path: %s", file_path)

        result = test_processor.can_process(file_path)
        logger.debug("can_process result: %s", result)
        assert result

    def test_can_process_unsupported_extension(
        self, test_processor: TestProcessor, tmp_path: Path, caplog: LogCaptureFixture
    ):
        """Test can_process with unsupported file extension.

        Args:
            test_processor: Test processor instance
            tmp_path: Temporary directory path
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing can_process with unsupported extension")

        file_path = tmp_path / "test.unsupported"
        logger.debug("Testing file path: %s", file_path)

        result = test_processor.can_process(file_path)
        logger.debug("can_process result: %s", result)
        assert not result

    def test_can_process_case_insensitive(self, tmp_path: Path, caplog: LogCaptureFixture):
        """Test can_process is case insensitive for extensions.

        Args:
            tmp_path: Temporary directory path
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing case-insensitive extension handling")

        processor = TestProcessor(supported_extensions={".TEST"})
        logger.debug(
            "Created processor with uppercase extension: %s", processor.supported_extensions
        )

        file_path = tmp_path / "test.test"
        logger.debug("Testing file path: %s", file_path)

        result = processor.can_process(file_path)
        logger.debug("can_process result: %s", result)
        assert result

    def test_multiple_supported_extensions(self, tmp_path: Path, caplog: LogCaptureFixture):
        """Test processor supporting multiple file extensions.

        Args:
            tmp_path: Temporary directory path
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing multiple supported extensions")

        processor = TestProcessor(supported_extensions={".test", ".mock"})
        logger.debug("Created processor with extensions: %s", processor.supported_extensions)

        test_file = tmp_path / "test.test"
        mock_file = tmp_path / "test.mock"
        unsupported_file = tmp_path / "test.unsupported"

        logger.debug("Testing file paths: %s, %s, %s", test_file, mock_file, unsupported_file)

        assert processor.can_process(test_file)
        assert processor.can_process(mock_file)
        assert not processor.can_process(unsupported_file)
        logger.debug("All extension tests passed")
