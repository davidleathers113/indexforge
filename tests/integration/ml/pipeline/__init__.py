"""Integration tests for ML pipeline functionality.

This package contains integration tests that verify the ML pipeline's functionality,
including strategy execution, dependency management, performance characteristics,
and resource management. Tests are organized into modules:

- test_strategy_pipeline.py: Basic pipeline functionality tests
- test_complex_pipeline.py: Advanced pipeline scenarios and edge cases
- test_pipeline_performance.py: Performance and resource management tests
"""

from .test_complex_pipeline import (
    TimedStrategy,
    test_complex_error_propagation,
    test_complex_metadata_chain,
    test_cyclic_dependency_detection,
    test_parallel_execution,
)
from .test_pipeline_performance import (
    ResourceIntensiveStrategy,
    test_concurrent_pipeline_execution,
    test_memory_usage,
    test_pipeline_resource_limits,
    test_processing_time,
)
from .test_strategy_pipeline import (
    MockStrategy,
    test_error_handling,
    test_metadata_propagation,
    test_result_caching,
    test_strategy_execution_order,
)

__all__ = [
    # Complex pipeline tests
    "TimedStrategy",
    "test_parallel_execution",
    "test_cyclic_dependency_detection",
    "test_complex_error_propagation",
    "test_complex_metadata_chain",
    # Performance tests
    "ResourceIntensiveStrategy",
    "test_memory_usage",
    "test_processing_time",
    "test_concurrent_pipeline_execution",
    "test_pipeline_resource_limits",
    # Strategy pipeline tests
    "MockStrategy",
    "test_strategy_execution_order",
    "test_metadata_propagation",
    "test_error_handling",
    "test_result_caching",
]
