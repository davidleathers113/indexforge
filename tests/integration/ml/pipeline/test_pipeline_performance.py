"""Integration tests for ML pipeline performance and resource management.

Tests pipeline performance characteristics including memory usage,
processing time, and resource cleanup under various loads.
"""

import asyncio
import gc
import logging
from typing import Any, Dict, List

import pytest
from src.core.metrics import MemoryTracker, TimeTracker
from src.ml.processing.models.strategies import ProcessingStrategy
from src.ml.processing.strategies.dependency import DependencyGraph
from src.ml.processing.strategies.pipeline import StrategyPipeline


class ResourceIntensiveStrategy(ProcessingStrategy):
    """Strategy that simulates resource-intensive processing."""

    def __init__(
        self,
        name: str,
        memory_mb: int,
        process_time: float,
        result: Any,
        dependencies: list[str] | None = None,
    ):
        self.name = name
        self.memory_mb = memory_mb
        self.process_time = process_time
        self.result = result
        self.dependencies = dependencies or []
        self._data: List[bytes] = []

    def validate(self, content: str) -> list[str]:
        """Validate input content."""
        return []

    async def process(self, content: str, metadata: dict | None = None) -> Any:
        """Process content with simulated resource usage."""
        # Allocate memory
        chunk_size = 1024 * 1024  # 1MB
        self._data = [b"0" * chunk_size for _ in range(self.memory_mb)]

        await asyncio.sleep(self.process_time)
        result = self.result

        # Cleanup
        self._data.clear()
        return result


@pytest.fixture
def performance_graph() -> DependencyGraph:
    """Create a graph for performance testing."""
    graph = DependencyGraph()
    # Linear chain with parallel branches
    graph.add_dependency("B1", "A")
    graph.add_dependency("B2", "A")
    graph.add_dependency("C", "B1")
    graph.add_dependency("C", "B2")
    return graph


@pytest.mark.asyncio
async def test_memory_usage(performance_graph: DependencyGraph, caplog):
    """Test memory usage during pipeline execution."""
    caplog.set_level(logging.INFO)
    strategies = {
        "A": ResourceIntensiveStrategy("A", memory_mb=10, process_time=0.1, result="A"),
        "B1": ResourceIntensiveStrategy("B1", memory_mb=20, process_time=0.2, result="B1", ["A"]),
        "B2": ResourceIntensiveStrategy("B2", memory_mb=20, process_time=0.2, result="B2", ["A"]),
        "C": ResourceIntensiveStrategy("C", memory_mb=10, process_time=0.1, result="C", ["B1", "B2"]),
    }

    pipeline = StrategyPipeline(performance_graph)
    memory_tracker = MemoryTracker()

    # Record baseline memory
    gc.collect()
    baseline_memory = memory_tracker.get_memory_mb()

    # Execute pipeline
    results = await pipeline.execute(strategies, "test content")

    # Check peak memory
    peak_memory = memory_tracker.get_peak_memory_mb()
    assert peak_memory - baseline_memory < 60  # Less than sum of all strategies (60MB)

    # Verify cleanup
    gc.collect()
    end_memory = memory_tracker.get_memory_mb()
    assert abs(end_memory - baseline_memory) < 1  # Memory returned to baseline


@pytest.mark.asyncio
async def test_processing_time(performance_graph: DependencyGraph):
    """Test processing time and parallel execution efficiency."""
    strategies = {
        "A": ResourceIntensiveStrategy("A", memory_mb=1, process_time=0.1, result="A"),
        "B1": ResourceIntensiveStrategy("B1", memory_mb=1, process_time=0.2, result="B1", ["A"]),
        "B2": ResourceIntensiveStrategy("B2", memory_mb=1, process_time=0.2, result="B2", ["A"]),
        "C": ResourceIntensiveStrategy("C", memory_mb=1, process_time=0.1, result="C", ["B1", "B2"]),
    }

    pipeline = StrategyPipeline(performance_graph)
    time_tracker = TimeTracker()

    # Execute pipeline and measure time
    with time_tracker:
        results = await pipeline.execute(strategies, "test content")

    total_time = time_tracker.elapsed_seconds
    sequential_time = sum(s.process_time for s in strategies.values())

    # Total time should be significantly less than sequential time
    # due to parallel execution of B1 and B2
    assert total_time < sequential_time * 0.8


@pytest.mark.asyncio
async def test_concurrent_pipeline_execution():
    """Test multiple pipeline executions running concurrently."""
    graph = DependencyGraph()
    graph.add_dependency("B", "A")

    async def run_pipeline(pipeline: StrategyPipeline, id: int) -> Dict[str, Any]:
        strategies = {
            "A": ResourceIntensiveStrategy(f"A{id}", memory_mb=5, process_time=0.2, result=f"A{id}"),
            "B": ResourceIntensiveStrategy(f"B{id}", memory_mb=5, process_time=0.2, result=f"B{id}", ["A"]),
        }
        return await pipeline.execute(strategies, f"content {id}")

    # Create multiple pipelines
    pipelines = [StrategyPipeline(graph) for _ in range(3)]
    memory_tracker = MemoryTracker()
    time_tracker = TimeTracker()

    # Record baseline
    gc.collect()
    baseline_memory = memory_tracker.get_memory_mb()

    # Execute pipelines concurrently
    with time_tracker:
        results = await asyncio.gather(*(
            run_pipeline(pipeline, i)
            for i, pipeline in enumerate(pipelines)
        ))

    # Verify results
    assert len(results) == 3
    for i, result in enumerate(results):
        assert result[f"A{i}"] == f"A{i}"
        assert result[f"B{i}"] == f"B{i}"

    # Verify performance
    total_time = time_tracker.elapsed_seconds
    assert total_time < 0.8  # Should be less than 2 * process_time due to concurrency

    # Verify cleanup
    gc.collect()
    end_memory = memory_tracker.get_memory_mb()
    assert abs(end_memory - baseline_memory) < 1


@pytest.mark.asyncio
async def test_pipeline_resource_limits(performance_graph: DependencyGraph, caplog):
    """Test pipeline behavior under resource constraints."""
    caplog.set_level(logging.WARNING)

    # Create strategies that use significant resources
    strategies = {
        "A": ResourceIntensiveStrategy("A", memory_mb=50, process_time=0.1, result="A"),
        "B1": ResourceIntensiveStrategy("B1", memory_mb=50, process_time=0.2, result="B1", ["A"]),
        "B2": ResourceIntensiveStrategy("B2", memory_mb=50, process_time=0.2, result="B2", ["A"]),
    }

    pipeline = StrategyPipeline(performance_graph)
    memory_tracker = MemoryTracker()

    # Execute pipeline with resource monitoring
    gc.collect()
    baseline_memory = memory_tracker.get_memory_mb()
    results = await pipeline.execute(strategies, "test content")

    # Verify memory usage and cleanup
    peak_memory = memory_tracker.get_peak_memory_mb()
    assert peak_memory - baseline_memory < 150  # Less than total allocated (150MB)

    # Check for memory warnings
    assert any(
        "High memory usage" in record.message
        for record in caplog.records
        if record.levelno >= logging.WARNING
    )

    # Verify cleanup
    gc.collect()
    end_memory = memory_tracker.get_memory_mb()
    assert abs(end_memory - baseline_memory) < 1
```