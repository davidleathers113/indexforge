"""System fixtures for testing.

This module provides system-related functionality:
- CLI components
- System components
- Monitoring
- Pipeline management
"""

from .cli import CLIState, mock_argparse_parse_args, mock_name_main, mock_sys_argv
from .components import ComponentState, mock_components
from .monitoring import MonitoringState, mock_monitor, mock_process, mock_prometheus
from .pipeline import PipelineState, mock_pipeline, pipeline_with_mocks


__all__ = [
    "CLIState",
    "ComponentState",
    "MonitoringState",
    "PipelineState",
    "mock_argparse_parse_args",
    "mock_components",
    "mock_monitor",
    "mock_name_main",
    "mock_pipeline",
    "mock_process",
    "mock_prometheus",
    "mock_sys_argv",
    "pipeline_with_mocks",
]
