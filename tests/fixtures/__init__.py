"""Test fixtures package."""

__all__ = [
    "ErrorState",
    "mock_api_error",
    "mock_auth_error",
    "mock_network_error",
    "mock_timeout_error",
    "mock_validation_error",
    "error_state",
    "LoggerState",
    "file_logger",
    "logger_state",
    "mock_logger",
    "mock_redis",
    "vector_state",
    "mock_weaviate_client",
    "DocumentState",
    "doc_state",
    "document_with_relationships",
    "large_document",
    "sample_data",
    "sample_document",
    "SearchState",
    "mock_search_executor",
    "mock_argparse_parse_args",
    "CLIState",
    "mock_name_main",
    "mock_sys_argv",
    "ComponentState",
    "component_state",
    "mock_components",
    "mock_monitor",
    "MonitoringState",
    "mock_process",
    "mock_prometheus",
    "mock_pipeline",
    "PipelineState",
    "pipeline_state",
    "pipeline_with_mocks",
    "TextState",
    "mock_encoding",
    "mock_tiktoken",
    "SummarizerState",
    "mock_summarizer_pipeline",
    "summarizer_state",
]

# Core utilities
from .core.errors import (
    ErrorState as ErrorState,
    error_state,
    mock_api_error as mock_api_error,
    mock_auth_error as mock_auth_error,
    mock_network_error as mock_network_error,
    mock_timeout_error as mock_timeout_error,
    mock_validation_error as mock_validation_error,
)
from .core.logger import (
    LoggerState as LoggerState,
    file_logger as file_logger,
    logger_state as logger_state,
    mock_logger as mock_logger,
)

# Data handling
from .data.redis import redis_mock as mock_redis
from .data.vector import VectorState as vector_state, mock_weaviate_client as mock_weaviate_client

# Document handling
from .documents import DocumentState as DocumentState, doc_state as doc_state
from .documents.fixtures import (
    document_with_relationships as document_with_relationships,
    large_document as large_document,
    sample_data as sample_data,
    sample_document as sample_document,
)

# Search functionality
from .search.executor import (
    SearchState as SearchState,
    mock_search_executor as mock_search_executor,
)

# System components
from .system.cli import (
    CLIState as CLIState,
    mock_argparse_parse_args as mock_argparse_parse_args,
    mock_name_main as mock_name_main,
    mock_sys_argv as mock_sys_argv,
)
from .system.components import (
    ComponentState as ComponentState,
    component_state as component_state,
    mock_components as mock_components,
)
from .system.monitoring import (
    MonitoringState as MonitoringState,
    mock_monitor as mock_monitor,
    mock_process as mock_process,
    mock_prometheus as mock_prometheus,
)
from .system.pipeline import (
    PipelineState as PipelineState,
    mock_pipeline as mock_pipeline,
    pipeline_state as pipeline_state,
    pipeline_with_mocks as pipeline_with_mocks,
)

# Text processing
from .text.processor import (
    TextState as TextState,
    mock_encoding as mock_encoding,
    mock_tiktoken as mock_tiktoken,
)
from .text.summarizer import (
    SummarizerState as SummarizerState,
    mock_summarizer_pipeline as mock_summarizer_pipeline,
    summarizer_state as summarizer_state,
)
