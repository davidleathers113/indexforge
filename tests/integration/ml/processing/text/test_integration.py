"""Integration tests for text processing pipeline.

Tests the interaction between different components of the text processing system.
"""

import pytest

from src.ml.processing.text.analysis import detect_language, validate_content
from src.ml.processing.text.chunking import chunk_text, merge_chunks
from src.ml.processing.text.cleaning import clean_text
from src.ml.processing.text.config import TextProcessingConfig
from src.ml.processing.text.processor import TextProcessor


@pytest.fixture
def sample_text():
    """Fixture providing sample text for testing."""
    return """First paragraph with multiple sentences. This is a test.

    Second paragraph here. It has some content.

    Third paragraph with special chars: @#$%^&*()
    """


@pytest.fixture
def processor():
    """Fixture providing configured text processor."""
    config = TextProcessingConfig(
        max_chunk_size=100, chunk_overlap=20, detect_language=True, min_confidence=0.8
    )
    return TextProcessor(config)


def test_full_processing_pipeline(sample_text, processor):
    """Test complete text processing pipeline."""
    # Initialize processor
    processor.initialize()

    try:
        # Clean and validate text
        cleaned_text = clean_text(sample_text)
        assert validate_content(cleaned_text)

        # Detect language
        lang = detect_language(cleaned_text)
        assert lang == "en"

        # Process text into chunks
        chunks = processor.chunk_text(cleaned_text)
        assert len(chunks) > 1

        # Verify chunk properties
        for chunk in chunks:
            assert len(chunk) <= processor.config.max_chunk_size
            assert validate_content(chunk)

        # Verify content preservation
        merged = merge_chunks(chunks)
        assert "First paragraph" in merged
        assert "Second paragraph" in merged
        assert "Third paragraph" in merged

    finally:
        processor.cleanup()


def test_pipeline_error_handling(processor):
    """Test error handling in processing pipeline."""
    with pytest.raises(ValueError):
        processor.chunk_text("")  # Empty text

    with pytest.raises(ValueError):
        processor.chunk_text("A" * 1000000)  # Too long

    with pytest.raises(RuntimeError):
        # Try to process without initialization
        new_processor = TextProcessor()
        new_processor.chunk_text("test")


def test_pipeline_configuration_changes(sample_text, processor):
    """Test pipeline behavior with configuration changes."""
    processor.initialize()

    try:
        # Process with initial config
        chunks1 = processor.chunk_text(sample_text)

        # Change configuration
        new_config = TextProcessingConfig(max_chunk_size=50, chunk_overlap=10)  # Smaller chunks
        processor.config = new_config

        # Process with new config
        chunks2 = processor.chunk_text(sample_text)

        # Verify different chunking behavior
        assert len(chunks2) > len(chunks1)
        assert all(len(chunk) <= 50 for chunk in chunks2)

    finally:
        processor.cleanup()


def test_pipeline_metadata_tracking(sample_text, processor):
    """Test metadata tracking throughout pipeline."""
    processor.initialize()

    try:
        # Process text and check metadata
        processor.chunk_text(sample_text)
        metadata = processor.get_metadata()

        assert "processed_chunks" in metadata
        assert "total_characters" in metadata
        assert "processing_time" in metadata
        assert isinstance(metadata["processed_chunks"], int)
        assert metadata["processed_chunks"] > 0

    finally:
        processor.cleanup()


def test_pipeline_concurrent_processing(processor):
    """Test pipeline handling concurrent processing."""
    processor.initialize()

    try:
        texts = ["First test document.", "Second test document.", "Third test document."]

        # Process multiple texts
        results = []
        for text in texts:
            chunks = processor.chunk_text(text)
            results.append(chunks)

        # Verify results
        assert len(results) == len(texts)
        assert all(len(chunks) > 0 for chunks in results)

        # Verify processor state
        metadata = processor.get_metadata()
        assert metadata["processed_chunks"] == sum(len(chunks) for chunks in results)

    finally:
        processor.cleanup()


def test_pipeline_resource_cleanup(processor):
    """Test proper resource cleanup in pipeline."""
    processor.initialize()
    processor.cleanup()

    # Verify processor state after cleanup
    with pytest.raises(RuntimeError):
        processor.chunk_text("test")  # Should fail after cleanup

    # Verify can reinitialize
    processor.initialize()
    try:
        chunks = processor.chunk_text("test")
        assert len(chunks) > 0
    finally:
        processor.cleanup()
