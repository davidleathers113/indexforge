"""Test configuration and shared fixtures."""

# Core fixtures
from .fixtures.core.logger import logger_state, mock_logger

# Data management
from .fixtures.data.cache import cache_state, mock_cache_manager
from .fixtures.data.docker import docker_services, redis_service, weaviate_service
from .fixtures.data.embedding import (
    OpenAIState,
    mock_embedding_generator,
    mock_openai,
    openai_state,
)
from .fixtures.data.redis import redis_mock as mock_redis
from .fixtures.data.vector import VectorState, mock_weaviate_client, vector_state

# Document handling
from .fixtures.documents.processor import mock_doc_processor
from .fixtures.documents.state import DocumentState, doc_state

# Processing utilities
from .fixtures.processing.pii import PIIState, mock_pii_detector, pii_state
from .fixtures.processing.topic import (  # Explicitly import all topic-related fixtures
    TopicState,
    mock_topic_clusterer,
    topic_state,
)

# Search functionality
from .fixtures.search.components import mock_search_components, mock_search_manager
from .fixtures.search.executor import mock_search_executor

# System components
from .fixtures.system.cli import (
    CLIState,
    mock_argparse_parse_args,
    mock_cli_state,
    mock_name_main,
    mock_sys_argv,
)
from .fixtures.system.components import ComponentState, component_state, mock_components
from .fixtures.system.pipeline import (
    PipelineState,
    mock_pipeline,
    pipeline_state,
    pipeline_with_mocks,
)

# Text processing
from .fixtures.text.summarizer import SummarizerState, mock_summarizer_pipeline, summarizer_state

# Re-export fixtures to ensure they're available
__all__ = [
    # Core
    "mock_logger",
    # Data management
    "mock_cache_manager",
    "cache_state",
    "mock_embedding_generator",
    "mock_openai",
    "openai_state",
    "OpenAIState",
    "vector_state",
    "VectorState",
    "mock_weaviate_client",
    "mock_redis",
    "docker_services",
    "redis_service",
    "weaviate_service",
    # Document handling
    "mock_doc_processor",
    "doc_state",
    "DocumentState",
    # Processing utilities
    "mock_pii_detector",
    "pii_state",
    "PIIState",
    "mock_topic_clusterer",
    "topic_state",
    "TopicState",
    # Search functionality
    "mock_search_components",
    "mock_search_manager",
    "mock_search_executor",
    # System components
    "mock_argparse_parse_args",
    "mock_name_main",
    "mock_sys_argv",
    "mock_cli_state",
    "CLIState",
    "mock_components",
    "component_state",
    "ComponentState",
    "mock_pipeline",
    "pipeline_with_mocks",
    "pipeline_state",
    "PipelineState",
    # Text processing
    "mock_summarizer_pipeline",
    "summarizer_state",
    "SummarizerState",
]

import tracemalloc

import pytest


def pytest_configure(config):
    """Configure pytest with enhanced exception handling and parallel safety."""
    try:
        tracemalloc.start()
    except RuntimeError:
        # Already started
        pass

    # Configure xdist worker settings
    if hasattr(config, "workerinput"):
        # Worker-specific initialization
        pass


def pytest_unconfigure(config):
    """Cleanup pytest configuration."""
    try:
        tracemalloc.stop()
    except RuntimeError:
        # Not running
        pass


@pytest.fixture(scope="session", autouse=True)
def configure_parallel_safety():
    """Ensure proper cleanup in parallel test execution."""
    yield
