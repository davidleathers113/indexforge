"""Tests for base processor functionality."""

from typing import Any, Dict

import pytest

from .base import BaseProcessor
from .config.settings import PipelineConfig, ProcessingConfig


class TestProcessor(BaseProcessor):
    """Test implementation of BaseProcessor."""

    def initialize(self) -> None:
        """Test initialization."""
        super().initialize()

    def process(self, data: Any) -> Dict[str, Any]:
        """Test processing."""
        super().process(data)
        return {"processed": data}


def test_default_initialization():
    """Test processor initialization with default config."""
    processor = TestProcessor()
    assert isinstance(processor.config, PipelineConfig)
    assert isinstance(processor.processing_config, ProcessingConfig)
    assert not processor.is_initialized


def test_custom_config():
    """Test processor initialization with custom config."""
    config = PipelineConfig(processing=ProcessingConfig(batch_size=200))
    processor = TestProcessor(config=config)
    assert processor.processing_config.batch_size == 200


def test_override_processing_config():
    """Test overriding processing config."""
    config = PipelineConfig()
    processing_config = ProcessingConfig(batch_size=300)
    processor = TestProcessor(config=config, processing_config=processing_config)
    assert processor.config.processing.batch_size == 100  # Default in main config
    assert processor.processing_config.batch_size == 300  # Overridden value


def test_invalid_processing_config():
    """Test validation of processing config type."""
    with pytest.raises(ValueError, match="must be an instance of ProcessingConfig"):
        TestProcessor(processing_config={"batch_size": 100})  # type: ignore


def test_initialization_state():
    """Test processor initialization state management."""
    processor = TestProcessor()
    assert not processor.is_initialized

    processor.initialize()
    assert processor.is_initialized

    processor.cleanup()
    assert not processor.is_initialized


def test_context_manager():
    """Test processor context manager functionality."""
    with TestProcessor() as processor:
        assert processor.is_initialized
        result = processor.process("test")
        assert result == {"processed": "test"}
    assert not processor.is_initialized


def test_process_without_initialization():
    """Test processing without initialization."""
    processor = TestProcessor()
    with pytest.raises(RuntimeError, match="must be initialized"):
        processor.process("test")
