"""Tests for text document processor."""

from pathlib import Path

import pytest

from .config.settings import PipelineConfig
from .text import TextProcessingConfig, TextProcessor


@pytest.fixture
def sample_text(tmp_path: Path) -> Path:
    """Create a sample text file for testing.

    Args:
        tmp_path: Pytest fixture providing temporary directory path

    Returns:
        Path to the created text file
    """
    file_path = tmp_path / "test.txt"

    # Create test content with paragraphs
    content = (
        "Title\n\n"
        "This is the first paragraph.\n"
        "It has multiple lines.\n\n"
        "This is the second paragraph.\n"
        "It also has multiple lines.\n"
    )

    # Write content to file
    file_path.write_text(content)

    return file_path


def test_default_initialization():
    """Test text processor initialization with default config."""
    processor = TextProcessor()
    assert isinstance(processor.config, PipelineConfig)
    assert isinstance(processor.processing_config, TextProcessingConfig)
    assert not processor.is_initialized
    assert len(processor.processed_files) == 0


def test_custom_config():
    """Test text processor with custom configuration."""
    config = TextProcessingConfig(
        detect_paragraphs=False, strip_whitespace=False, max_line_length=500
    )
    processor = TextProcessor(processing_config=config)
    assert not processor.processing_config.detect_paragraphs
    assert not processor.processing_config.strip_whitespace
    assert processor.processing_config.max_line_length == 500


def test_process_text_file(sample_text: Path):
    """Test processing of a valid text file."""
    processor = TextProcessor()

    with processor:
        result = processor.process(sample_text)

    assert isinstance(result, dict)
    assert "content" in result
    assert "metadata" in result
    assert "structure" in result

    # Check metadata
    assert result["metadata"]["file_path"] == str(sample_text)
    assert result["metadata"]["file_type"] == ".txt"
    assert result["metadata"]["total_lines"] > 0
    assert result["metadata"]["detect_paragraphs"] is True

    # Check structure
    assert len(result["structure"]) > 0
    assert all(isinstance(line["text"], str) for line in result["structure"])
    assert all("length" in line for line in result["structure"])

    # Check processed files tracking
    assert sample_text in processor.processed_files


def test_paragraph_detection(sample_text: Path):
    """Test paragraph detection functionality."""
    config = TextProcessingConfig(detect_paragraphs=True, strip_whitespace=True)
    processor = TextProcessor(processing_config=config)

    with processor:
        result = processor.process(sample_text)

    # Verify paragraphs are preserved in content
    content = result["content"]
    assert "first paragraph" in content
    assert "second paragraph" in content

    # Check structure reflects paragraph breaks
    structure = result["structure"]
    assert len(structure) > 2  # Should have multiple lines


def test_whitespace_handling(tmp_path: Path):
    """Test whitespace handling options."""
    # Create file with excess whitespace
    file_path = tmp_path / "whitespace.txt"
    content = "  Line with spaces  \n\t\tTabbed line\t\t\n"
    file_path.write_text(content)

    # Test with whitespace stripping
    config = TextProcessingConfig(strip_whitespace=True)
    processor = TextProcessor(processing_config=config)

    with processor:
        result = processor.process(file_path)

    # Check whitespace is stripped
    assert all(not line["text"].startswith(" ") for line in result["structure"])
    assert all(not line["text"].endswith(" ") for line in result["structure"])


def test_invalid_file_path():
    """Test processing with invalid file path."""
    processor = TextProcessor()
    with processor:
        with pytest.raises(ValueError, match="File not found"):
            processor.process(Path("nonexistent.txt"))


def test_invalid_file_type(tmp_path: Path):
    """Test processing with invalid file type."""
    invalid_file = tmp_path / "test.doc"
    invalid_file.touch()

    processor = TextProcessor()
    with processor:
        with pytest.raises(ValueError, match="Unsupported file type"):
            processor.process(invalid_file)


def test_line_length_limit(tmp_path: Path):
    """Test line length limit enforcement."""
    file_path = tmp_path / "test.txt"
    content = "x" * 2000  # Exceeds default limit
    file_path.write_text(content)

    processor = TextProcessor()
    with processor:
        with pytest.raises(ValueError, match="Line exceeds maximum length"):
            processor.process(file_path)


def test_cleanup():
    """Test cleanup of processor resources."""
    processor = TextProcessor()
    processor._processed_files.add(Path("test.txt"))

    processor.cleanup()
    assert len(processor.processed_files) == 0
    assert not processor.is_initialized
