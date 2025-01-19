"""Integration tests for ML strategy pipeline.

Tests the core functionality of the strategy pipeline, including strategy execution,
dependency management, and result handling.
"""

import pytest

from src.ml.processing.models.strategies import ProcessingStrategy
from src.ml.processing.strategies.dependency import DependencyGraph
from src.ml.processing.strategies.error_handling import StrategyExecutionError
from src.ml.processing.strategies.pipeline import StrategyPipeline


class MockStrategy(ProcessingStrategy):
    """Mock strategy for testing."""

    def __init__(self, name: str, result: str, dependencies: list[str] | None = None):
        self.name = name
        self.result = result
        self.dependencies = dependencies or []
        self.called = False

    def validate(self, content: str) -> list[str]:
        """Validate input content."""
        return []

    async def process(self, content: str, metadata: dict | None = None) -> str:
        """Process content and return result."""
        self.called = True
        return self.result


@pytest.fixture
def dependency_graph() -> DependencyGraph:
    """Create a test dependency graph."""
    graph = DependencyGraph()
    graph.add_dependency("B", "A")  # B depends on A
    graph.add_dependency("C", "B")  # C depends on B
    return graph


@pytest.fixture
def strategies() -> dict[str, MockStrategy]:
    """Create test strategies."""
    return {
        "A": MockStrategy("A", "Result A"),
        "B": MockStrategy("B", "Result B", ["A"]),
        "C": MockStrategy("C", "Result C", ["B"]),
    }


@pytest.mark.asyncio
async def test_strategy_execution_order(
    dependency_graph: DependencyGraph,
    strategies: dict[str, MockStrategy],
):
    """Test that strategies are executed in correct dependency order."""
    pipeline = StrategyPipeline(dependency_graph)
    results = await pipeline.execute(strategies, "test content")

    # Verify execution order through results
    assert list(results.keys()) == ["A", "B", "C"]
    assert all(strategy.called for strategy in strategies.values())


@pytest.mark.asyncio
async def test_metadata_propagation(
    dependency_graph: DependencyGraph,
):
    """Test metadata propagation between strategies."""
    strategies = {
        "A": MockStrategy("A", {"result": "A", "metadata": {"key_a": "value_a"}}),
        "B": MockStrategy("B", {"result": "B", "metadata": {"key_b": "value_b"}}, ["A"]),
    }

    pipeline = StrategyPipeline(dependency_graph)
    results = await pipeline.execute(strategies, "test content")

    assert results["A"]["metadata"]["key_a"] == "value_a"
    assert results["B"]["metadata"]["key_b"] == "value_b"


@pytest.mark.asyncio
async def test_error_handling(dependency_graph: DependencyGraph):
    """Test error handling during strategy execution."""

    class ErrorStrategy(MockStrategy):
        async def process(self, content: str, metadata: dict | None = None) -> str:
            raise ValueError("Test error")

    strategies = {
        "A": MockStrategy("A", "Result A"),
        "B": ErrorStrategy("B", "Result B", ["A"]),
        "C": MockStrategy("C", "Result C", ["B"]),
    }

    pipeline = StrategyPipeline(dependency_graph)
    with pytest.raises(StrategyExecutionError) as exc_info:
        await pipeline.execute(strategies, "test content")

    assert "Test error" in str(exc_info.value)
    assert strategies["A"].called  # A should have executed
    assert not strategies["C"].called  # C should not have executed due to B's error


@pytest.mark.asyncio
async def test_result_caching(
    dependency_graph: DependencyGraph,
    strategies: dict[str, MockStrategy],
):
    """Test that strategy results are properly cached."""
    pipeline = StrategyPipeline(dependency_graph)
    await pipeline.execute(strategies, "test content")

    # Verify results are cached
    assert pipeline.get_result("A") == "Result A"
    assert pipeline.get_result("B") == "Result B"
    assert pipeline.get_result("C") == "Result C"

    # Clear cache and verify
    pipeline.clear_cache()
    assert pipeline.get_result("A") is None
