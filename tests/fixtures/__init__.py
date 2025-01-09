"""Test fixtures package."""

# Core functionality
from .core.base import BaseState  # noqa: F401
from .core.errors import error_state  # noqa: F401
from .core.errors import (
    ErrorState,
    mock_api_error,
    mock_auth_error,
    mock_network_error,
    mock_timeout_error,
    mock_validation_error,
)
from .core.logger import LoggerState, file_logger, logger_state, mock_logger  # noqa: F401

# Data management
from .data.cache import CacheState, cache_state, mock_cache_manager  # noqa: F401
from .data.embedding import mock_embedding_generator  # noqa: F401
from .data.redis import redis_mock as mock_redis  # noqa: F401
from .data.vector import VectorState as vector_state  # noqa: F401
from .data.vector import mock_weaviate_client

# Document handling
from .documents import mock_doc_processor  # noqa: F401
from .documents import sample_documents  # noqa: F401
from .documents import DocumentState, doc_state  # noqa: F401
from .documents.fixtures import document_with_relationships  # noqa: F401
from .documents.fixtures import large_document, sample_data, sample_document

# Processing utilities
from .processing import PIIState, TopicState, mock_pii_detector, mock_topic_clusterer  # noqa: F401

# Schema management
from .schema import SchemaState, mock_schema_validator  # noqa: F401

# Search functionality
from .search.components import mock_search_components, mock_search_manager  # noqa: F401
from .search.executor import SearchState, mock_search_executor  # noqa: F401
from .system.cli import mock_argparse_parse_args  # noqa: F401
from .system.cli import CLIState, mock_name_main, mock_sys_argv

# System components
from .system.components import ComponentState, component_state, mock_components  # noqa: F401
from .system.monitoring import mock_monitor  # noqa: F401
from .system.monitoring import MonitoringState, mock_process, mock_prometheus
from .system.pipeline import mock_pipeline  # noqa: F401
from .system.pipeline import PipelineState, pipeline_state, pipeline_with_mocks

# Text processing
from .text.processor import TextState, mock_encoding, mock_tiktoken  # noqa: F401
from .text.summarizer import SummarizerState  # noqa: F401
from .text.summarizer import mock_summarizer_pipeline, summarizer_state
