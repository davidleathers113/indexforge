"""Unit tests for base document processor.

Tests the functionality of the base document processor implementation.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.ml.processing.document.base import BaseDocumentProcessor, ProcessingResult
from src.ml.processing.document.config import DocumentProcessingConfig
from src.ml.processing.document.errors import (
    DocumentError,
    DocumentProcessingError,
    DocumentValidationError,
    UnsupportedDocumentError,
)


class TestProcessor(BaseDocumentProcessor):
    """Test implementation of BaseDocumentProcessor."""

    def _initialize_resources(self) -> None:
        """Initialize test resources."""
        pass

    def _cleanup_resources(self) -> None:
        """Clean up test resources."""
        pass

    def _process_document(self, file_path: Path) -> ProcessingResult:
        """Process test document."""
        return ProcessingResult(status="success", content="Test content", errors=[])


@pytest.fixture
def processor():
    """Create a test processor instance."""
    return TestProcessor()


@pytest.fixture
def config():
    """Create a test configuration."""
    return DocumentProcessingConfig(
        max_file_size=1000000,
        supported_extensions={".txt", ".doc"},
        extract_metadata=True,
        validate_content=True,
        chunk_size=1000,
    )


def test_processor_initialization(processor):
    """Test processor initialization."""
    assert not processor.is_initialized
    processor.initialize()
    assert processor.is_initialized
    processor.cleanup()
    assert not processor.is_initialized


def test_processor_context_manager(processor):
    """Test processor context manager functionality."""
    with processor as p:
        assert p.is_initialized
    assert not processor.is_initialized


def test_processor_custom_config(config):
    """Test processor with custom configuration."""
    processor = TestProcessor(config=config)
    assert processor.config.max_file_size == 1000000
    assert processor.config.supported_extensions == {".txt", ".doc"}
    assert processor.config.extract_metadata is True


def test_can_process(processor, tmp_path):
    """Test file type validation."""
    test_file = tmp_path / "test.txt"
    test_file.touch()

    processor.config.supported_extensions = {".txt"}
    assert processor.can_process(test_file)

    unsupported_file = tmp_path / "test.doc"
    unsupported_file.touch()
    assert not processor.can_process(unsupported_file)


def test_process_without_initialization(processor, tmp_path):
    """Test processing without initialization."""
    test_file = tmp_path / "test.txt"
    test_file.touch()

    with pytest.raises(DocumentError):
        processor.process(test_file)


def test_process_unsupported_file(processor, tmp_path):
    """Test processing unsupported file type."""
    test_file = tmp_path / "test.unsupported"
    test_file.touch()

    processor.initialize()
    with pytest.raises(UnsupportedDocumentError):
        processor.process(test_file)
    processor.cleanup()


def test_process_nonexistent_file(processor):
    """Test processing nonexistent file."""
    processor.initialize()
    with pytest.raises(DocumentValidationError):
        processor.process(Path("nonexistent.txt"))
    processor.cleanup()


def test_process_oversized_file(processor, tmp_path):
    """Test processing oversized file."""
    test_file = tmp_path / "test.txt"
    test_file.touch()

    # Mock file size check
    with patch("src.ml.processing.document.base.Path.stat") as mock_stat:
        mock_stat.return_value = Mock(st_size=2000000)
        processor.config.max_file_size = 1000000
        processor.initialize()

        with pytest.raises(DocumentValidationError):
            processor.process(test_file)

        processor.cleanup()


def test_successful_processing(processor, tmp_path):
    """Test successful document processing."""
    test_file = tmp_path / "test.txt"
    test_file.touch()

    processor.initialize()
    result = processor.process(test_file)
    processor.cleanup()

    assert isinstance(result, ProcessingResult)
    assert result.status == "success"
    assert result.content == "Test content"
    assert not result.errors


def test_metadata_tracking(processor, tmp_path):
    """Test metadata tracking during processing."""
    test_file = tmp_path / "test.txt"
    test_file.touch()

    processor.initialize()
    processor.process(test_file)
    metadata = processor.get_metadata()
    processor.cleanup()

    assert isinstance(metadata, dict)
    assert "processed_files" in metadata
    assert "total_size" in metadata
    assert "error_count" in metadata


def test_error_handling(processor, tmp_path):
    """Test error handling during processing."""
    test_file = tmp_path / "test.txt"
    test_file.touch()

    def failing_process(self, file_path):
        raise DocumentProcessingError("Processing failed")

    # Patch the _process_document method to simulate failure
    with patch.object(TestProcessor, "_process_document", failing_process):
        processor.initialize()
        with pytest.raises(DocumentProcessingError):
            processor.process(test_file)
        processor.cleanup()


def test_cleanup_error_handling(processor):
    """Test error handling during cleanup."""

    def failing_cleanup(self):
        raise DocumentError("Cleanup failed")

    # Patch the _cleanup_resources method to simulate failure
    with patch.object(TestProcessor, "_cleanup_resources", failing_cleanup):
        processor.initialize()
        with pytest.raises(DocumentError):
            processor.cleanup()
