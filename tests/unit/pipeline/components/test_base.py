"""Tests for the base pipeline component."""
import logging
from unittest.mock import MagicMock

import pytest

from src.pipeline.components.base import PipelineComponent
from src.pipeline.config.settings import PipelineConfig


class TestComponent(PipelineComponent):
    """Test implementation of PipelineComponent."""

    def process(self, documents: list[dict], **kwargs) -> list[dict]:
        """Process documents."""
        return documents


@pytest.fixture
def config():
    """Create a test configuration."""
    return PipelineConfig(export_dir='test_dir')


@pytest.fixture
def logger():
    """Create a test logger."""
    return MagicMock(spec=logging.Logger)


def test_component_initialization(config, logger):
    """Test component initialization."""
    component = TestComponent(config=config, logger=logger)
    assert component.config == config
    assert component.logger == logger


def test_component_default_logger(config):
    """Test component uses default logger if none provided."""
    component = TestComponent(config=config)
    assert isinstance(component.logger, logging.Logger)
    assert component.logger.name == 'TestComponent'


def test_component_process(config, logger):
    """Test component process method."""
    component = TestComponent(config=config, logger=logger)
    documents = [{'id': '1'}, {'id': '2'}]
    result = component.process(documents)
    assert result == documents


def test_component_cleanup(config, logger):
    """Test component cleanup method."""
    component = TestComponent(config=config, logger=logger)
    component.cleanup()