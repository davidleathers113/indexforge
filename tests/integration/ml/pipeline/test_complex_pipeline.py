"""Integration tests for complex ML pipeline scenarios.

Tests advanced pipeline functionality including cyclic dependencies,
parallel execution, and complex error propagation.
"""

import asyncio
from typing import Any, Dict

import pytest

from src.ml.processing.models.strategies import ProcessingStrategy
from src.ml.processing.strategies.dependency import CyclicDependencyError, DependencyGraph
from src.ml.processing.strategies.error_handling import StrategyExecutionError
from src.ml.processing.strategies.pipeline import StrategyPipeline


class TimedStrategy(ProcessingStrategy):
    """Strategy that simulates processing time."""

    def __init__(
        self,
        name: str,
        process_time: float,
        result: Any,
        dependencies: list[str] | None = None,
        should_fail: bool = False,
    ):
        self.name = name
        self.process_time = process_time
        self.result = result
        self.dependencies = dependencies or []
        self.should_fail = should_fail
        self.start_time = 0.0
        self.end_time = 0.0

    def validate(self, content: str) -> list[str]:
        """Validate input content."""
        return []

    async def process(self, content: str, metadata: dict | None = None) -> Any:
        """Process content with simulated delay."""
        self.start_time = asyncio.get_event_loop().time()
        await asyncio.sleep(self.process_time)

        if self.should_fail:
            raise ValueError(f"Strategy {self.name} failed")

        self.end_time = asyncio.get_event_loop().time()
        return self.result


@pytest.fixture
def complex_graph() -> DependencyGraph:
    """Create a complex dependency graph for testing."""
    graph = DependencyGraph()
    # A -> B -> D
    # A -> C -> D
    # E (independent)
    graph.add_dependency("B", "A")
    graph.add_dependency("C", "A")
    graph.add_dependency("D", "B")
    graph.add_dependency("D", "C")
    return graph


@pytest.mark.asyncio
async def test_parallel_execution(complex_graph: DependencyGraph):
    """Test that independent strategies execute in parallel."""
    strategies = {
        "A": TimedStrategy("A", 0.1, "Result A"),
        "B": TimedStrategy("B", 0.2, "Result B", ["A"]),
        "C": TimedStrategy("C", 0.2, "Result C", ["A"]),
        "D": TimedStrategy("D", 0.1, "Result D", ["B", "C"]),
        "E": TimedStrategy("E", 0.3, "Result E"),
    }

    pipeline = StrategyPipeline(complex_graph)
    start_time = asyncio.get_event_loop().time()
    results = await pipeline.execute(strategies, "test content")
    total_time = asyncio.get_event_loop().time() - start_time

    # Verify results
    assert len(results) == 5
    # B and C should run in parallel after A
    b_strategy = strategies["B"]
    c_strategy = strategies["C"]
    assert abs(b_strategy.start_time - c_strategy.start_time) < 0.1
    # Total time should be less than sum of individual times
    assert total_time < sum(s.process_time for s in strategies.values())


@pytest.mark.asyncio
async def test_cyclic_dependency_detection():
    """Test detection of cyclic dependencies."""
    graph = DependencyGraph()
    # Create a cycle: A -> B -> C -> A
    graph.add_dependency("B", "A")
    graph.add_dependency("C", "B")

    with pytest.raises(CyclicDependencyError):
        graph.add_dependency("A", "C")


@pytest.mark.asyncio
async def test_complex_error_propagation(complex_graph: DependencyGraph):
    """Test error propagation in complex dependency chains."""
    strategies = {
        "A": TimedStrategy("A", 0.1, "Result A"),
        "B": TimedStrategy("B", 0.2, "Result B", ["A"], should_fail=True),
        "C": TimedStrategy("C", 0.2, "Result C", ["A"]),
        "D": TimedStrategy("D", 0.1, "Result D", ["B", "C"]),
    }

    pipeline = StrategyPipeline(complex_graph)
    with pytest.raises(StrategyExecutionError) as exc_info:
        await pipeline.execute(strategies, "test content")

    # Verify error propagation
    assert "Strategy B failed" in str(exc_info.value)
    assert strategies["A"].end_time > 0  # A completed
    assert strategies["C"].end_time > 0  # C completed (independent of B's failure)
    assert strategies["D"].end_time == 0  # D never started due to B's failure


@pytest.mark.asyncio
async def test_complex_metadata_chain(complex_graph: DependencyGraph):
    """Test metadata propagation in complex dependency chains."""
    strategies = {
        "A": TimedStrategy("A", 0.1, {"result": "A", "metadata": {"key_a": "value_a"}}),
        "B": TimedStrategy("B", 0.1, {"result": "B", "metadata": {"key_b": "value_b"}}, ["A"]),
        "C": TimedStrategy("C", 0.1, {"result": "C", "metadata": {"key_c": "value_c"}}, ["A"]),
        "D": TimedStrategy("D", 0.1, {"result": "D", "metadata": {"key_d": "value_d"}}, ["B", "C"]),
    }

    pipeline = StrategyPipeline(complex_graph)
    results = await pipeline.execute(strategies, "test content")

    # Verify metadata propagation
    assert results["A"]["metadata"]["key_a"] == "value_a"
    assert results["B"]["metadata"]["key_b"] == "value_b"
    assert results["C"]["metadata"]["key_c"] == "value_c"
    assert results["D"]["metadata"]["key_d"] == "value_d"

    # D should have access to all previous metadata
    d_metadata = results["D"]["metadata"]
    assert all(d_metadata.get(f"key_{key}") == f"value_{key}" for key in ["a", "b", "c", "d"])
