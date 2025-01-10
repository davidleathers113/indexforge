"""Core pipeline fixtures.

This module has been refactored into smaller, more focused modules under the pipeline/ directory.
It is maintained for backward compatibility.
"""

from .pipeline.component_mocks import pipeline_with_mocks
from .pipeline.mock_pipeline import mock_pipeline
from .pipeline.pipeline_state import PipelineState, pipeline_state

__all__ = [
    "pipeline_state",
    "PipelineState",
    "mock_pipeline",
    "pipeline_with_mocks",
]
