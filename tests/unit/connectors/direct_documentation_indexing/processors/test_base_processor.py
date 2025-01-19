"""Tests for the BaseProcessor class."""

import logging
from pathlib import Path
from typing import Any

from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture
import pytest

from src.core.processors.base import BaseProcessor, ProcessingResult


# Configure logging for the test module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestProcessor(BaseProcessor):
    """Test implementation of BaseProcessor."""

    def __init__(
        self, config: dict[str, Any] | None = None, logger: logging.Logger | None = None
    ):
        """Initialize the test processor.

        Args:
            config: Optional configuration dictionary
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.logger.debug(
            "Initializing TestProcessor with config=%s, logger=%s",
            config,
            "custom" if logger else "default",
        )
        super().__init__(config)
        self.supported_extensions = {".test"}
        self.logger.info(
            "TestProcessor initialized with supported extensions=%s", self.supported_extensions
        )

    def can_process(self, file_path: Path | str) -> bool:
        """Check if file can be processed.

        Args:
            file_path: Path to the file to check

        Returns:
            bool: True if the file can be processed, False otherwise
        """
        self.logger.debug("Checking if file can be processed: %s", file_path)
        try:
            if isinstance(file_path, str):
                file_path = Path(file_path)
            result = file_path.suffix in self.supported_extensions
            self.logger.info(
                "File %s can%s be processed (extension=%s)",
                file_path,
                "" if result else "not",
                file_path.suffix,
            )
            return result
        except Exception:
            self.logger.exception("Error checking if file can be processed: %s", file_path)
            return False

    def process(self, file_path: Path | str) -> ProcessingResult:
        """Process the file and return result.

        Args:
            file_path: Path to the file to process

        Returns:
            ProcessingResult: Result of the processing operation

        Raises:
            OSError: If the file cannot be accessed or processed
        """
        self.logger.debug("Starting to process file: %s", file_path)
        try:
            if isinstance(file_path, str):
                file_path = Path(file_path)

            if not file_path.exists():
                error_msg = f"File not found: {file_path}"
                self.logger.error(error_msg)
                raise OSError(error_msg)

            metadata = self._get_file_metadata(file_path)
            self.logger.debug("Retrieved metadata: %s", metadata)

            result = ProcessingResult(
                status="success",
                content={"text": "test content"},
            )
            self.logger.info("Successfully processed file: %s", file_path)
            return result

        except OSError:
            self.logger.exception("OSError processing file: %s", file_path)
            raise
        except Exception as e:
            self.logger.exception("Error processing file: %s", file_path)
            return ProcessingResult.create_error(str(e))


@pytest.fixture
def processor(caplog: LogCaptureFixture, request: FixtureRequest) -> TestProcessor:
    """Create a test processor instance.

    Args:
        caplog: Pytest fixture for capturing log messages
        request: Pytest fixture request object for test context

    Returns:
        TestProcessor: Configured test processor instance
    """
    caplog.set_level(logging.DEBUG)
    logger.info("Creating TestProcessor for test: %s", request.node.name)
    processor = TestProcessor()
    logger.debug(
        "TestProcessor created successfully with extensions=%s", processor.supported_extensions
    )
    return processor


@pytest.fixture
def sample_file(tmp_path: Path, request: FixtureRequest) -> Path:
    """Create a test file.

    Args:
        tmp_path: Pytest fixture for temporary directory
        request: Pytest fixture request object for test context

    Returns:
        Path: Path to created test file
    """
    logger.info("Creating sample file for test: %s", request.node.name)
    file_path = tmp_path / "test.test"
    file_path.write_text("test content")
    logger.debug("Created sample file at: %s (size=%d bytes)", file_path, file_path.stat().st_size)
    return file_path


def test_initialization(processor: TestProcessor, caplog: LogCaptureFixture):
    """Test processor initialization."""
    logger.info("Testing processor initialization")

    # Verify processor instance
    assert isinstance(
        processor, BaseProcessor
    ), f"Expected BaseProcessor instance, got {type(processor)}"
    assert processor.logger is not None, "Logger should not be None"
    assert processor.supported_extensions == {
        ".test"
    }, f"Expected supported_extensions={{'.test'}}, got {processor.supported_extensions}"

    # Verify initialization logs - check both setup and call phases
    init_logs = [
        record
        for record in caplog.get_records("setup") + caplog.get_records("call")
        if "TestProcessor initialized with supported extensions" in record.message
    ]
    assert (
        init_logs
    ), "Expected initialization log message not found. Available logs:\n" + "\n".join(
        f"- {record.message}" for record in caplog.records
    )

    logger.debug("Processor initialization test completed successfully")


def test_can_process_file(processor: TestProcessor, sample_file: Path, caplog: LogCaptureFixture):
    """Test file processing capability check."""
    logger.info("Testing file processing capability")

    # Test supported extension
    logger.debug("Testing supported file extension: %s", sample_file.suffix)
    assert (
        processor.can_process(sample_file) is True
    ), f"Should be able to process file with extension {sample_file.suffix}"

    # Test unsupported extension
    unsupported_file = Path("test.unsupported")
    logger.debug("Testing unsupported file extension: %s", unsupported_file.suffix)
    assert not processor.can_process(
        unsupported_file
    ), f"Should not be able to process file with extension {unsupported_file.suffix}"

    logger.debug("File processing capability test completed successfully")


def test_process_file_success(
    processor: TestProcessor, sample_file: Path, caplog: LogCaptureFixture
):
    """Test successful file processing."""
    logger.info("Testing successful file processing")

    logger.debug("Processing sample file: %s", sample_file)
    result = processor.process(sample_file)

    # Verify result
    logger.debug("Verifying processing result: %s", result)
    assert result.status == "success", f"Expected status 'success', got '{result.status}'"
    assert result.content == {
        "text": "test content"
    }, f"Expected content {{'text': 'test content'}}, got {result.content}"

    # Verify logs
    success_logs = [
        record for record in caplog.records if "Successfully processed file" in record.message
    ]
    assert success_logs, "Expected success log message not found. Available logs:\n" + "\n".join(
        f"- {record.message}" for record in caplog.records
    )

    logger.debug("File processing success test completed")


def test_invalid_file_path(processor: TestProcessor, caplog: LogCaptureFixture):
    """Test handling of invalid file paths."""
    logger.info("Testing invalid file path handling")

    invalid_path = Path("nonexistent.test")
    logger.debug("Attempting to process invalid file: %s", invalid_path)

    with pytest.raises(OSError) as exc_info:
        processor.process(invalid_path)

    # Verify error message
    error_msg = str(exc_info.value)
    assert (
        "File not found" in error_msg
    ), f"Expected 'File not found' in error message, got: {error_msg}"

    # Verify error logs
    error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
    assert error_logs, "Expected error log messages not found. Available logs:\n" + "\n".join(
        f"- {record.message}" for record in caplog.records
    )

    logger.debug("Invalid file path test completed successfully")


def test_create_error(caplog: LogCaptureFixture):
    """Test error result creation."""
    logger.info("Testing error result creation")

    # Create error result
    error_msg = "Test error"
    content = {"partial": "data"}
    logger.debug("Creating error result with message=%s, content=%s", error_msg, content)

    result = ProcessingResult.create_error(error_msg, content)

    # Verify result
    logger.debug("Verifying error result: %s", result)
    assert result.status == "error", f"Expected status 'error', got '{result.status}'"
    assert result.error == error_msg, f"Expected error '{error_msg}', got '{result.error}'"
    assert result.content == content, f"Expected content {content}, got {result.content}"

    logger.debug("Error result creation test completed successfully")
