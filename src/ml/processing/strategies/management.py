"""Legacy strategy management implementation.

This module is maintained for backward compatibility.
New code should use ModernStrategyManager instead.
"""

from typing import Any, TypeVar
import warnings

from src.ml.processing.errors import ServiceInitializationError
from src.ml.processing.models.strategies import ProcessingStrategy

from .dependency import DependencyGraph
from .factory import StrategyFactory
from .pipeline import StrategyPipeline


T = TypeVar("T")


class StrategyManager:
    """Legacy strategy management implementation.

    Warning:
        This class is maintained for backward compatibility.
        New code should use ModernStrategyManager instead.

    This implementation uses the modern components internally
    while maintaining the original interface.
    """

    def __init__(self) -> None:
        """Initialize the strategy manager."""
        warnings.warn(
            "StrategyManager is deprecated. Use ModernStrategyManager for new code.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._factory = StrategyFactory()
        self._graph = DependencyGraph()
        self._pipeline = StrategyPipeline(self._graph)

    @property
    def strategies(self) -> list[ProcessingStrategy[T]]:
        """Get the list of registered strategies."""
        return list(self._factory.get_strategies().values())

    def add_strategy(self, strategy: ProcessingStrategy[T]) -> None:
        """Add a processing strategy.

        Args:
            strategy: Strategy to add

        Raises:
            ValueError: If strategy is None or invalid
            ServiceInitializationError: If adding strategy would create circular dependency
        """
        if strategy is None:
            raise ValueError("Strategy cannot be None")

        strategy_name = strategy.__class__.__name__

        # Register the strategy class if not already registered
        if strategy_name not in self._factory._registry:
            self._factory.register(
                strategy_name, strategy.__class__, self._factory._dependencies.get(strategy_name)
            )

            # Add any dependencies to the graph
            deps = self._factory.get_dependencies(strategy_name)
            if deps:
                self._graph.add_dependencies(strategy_name, deps)

        # Cache the instance
        self._factory._instances[strategy_name] = strategy

    def validate_dependencies(self) -> None:
        """Validate that strategies are added in a valid order."""
        try:
            # Using dependency graph's execution order to validate
            self._graph.get_execution_order()
        except ServiceInitializationError as e:
            # Convert to original error format
            raise ServiceInitializationError(str(e), service_name=e.service_name)

    async def execute_pipeline(
        self, content: str, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute all strategies in optimized order.

        Args:
            content: Content to process
            metadata: Optional metadata to pass to strategies

        Returns:
            Dictionary mapping strategy names to their results

        Raises:
            StrategyExecutionError: If any strategy fails
        """
        return await self._pipeline.execute(self._factory.get_strategies(), content, metadata)

    def clear(self) -> None:
        """Remove all registered strategies."""
        self._factory.clear()
        self._graph.clear()
        self._pipeline.clear_cache()
