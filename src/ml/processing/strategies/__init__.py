"""Strategy implementations for text processing."""

from typing import Dict, Optional, Set, Type

from src.ml.processing.models.strategies import ProcessingStrategy

from .dependency import DependencyGraph
from .error_handling import ErrorHandler, StrategyExecutionError
from .factory import StrategyFactory
from .management import StrategyManager  # Keep for backward compatibility
from .nlp import NERStrategy, SentimentStrategy, TokenizationStrategy
from .pipeline import StrategyPipeline
from .topic import TopicStrategy


class ModernStrategyManager:
    """Modern facade for strategy management system.

    This class provides a clean interface to the strategy management system
    while maintaining the original functionality of StrategyManager.
    """

    def __init__(self) -> None:
        """Initialize the strategy manager."""
        self._factory = StrategyFactory()
        self._graph = DependencyGraph()
        self._pipeline = StrategyPipeline(self._graph)

        # Register built-in strategies
        self._register_builtin_strategies()

    def _register_builtin_strategies(self) -> None:
        """Register built-in strategy implementations."""
        strategies: Dict[str, Type[ProcessingStrategy]] = {
            "TokenizationStrategy": TokenizationStrategy,
            "NERStrategy": NERStrategy,
            "SentimentStrategy": SentimentStrategy,
            "TopicStrategy": TopicStrategy,
        }

        for name, strategy_class in strategies.items():
            self._factory.register(name, strategy_class)
            deps = self._factory.get_dependencies(name)
            if deps:
                self._graph.add_dependencies(name, deps)

    def register_strategy(
        self,
        name: str,
        strategy_class: Type[ProcessingStrategy],
        dependencies: Optional[Set[str]] = None,
    ) -> None:
        """Register a new strategy.

        Args:
            name: Name of the strategy
            strategy_class: Strategy class to register
            dependencies: Optional set of strategy dependencies
        """
        self._factory.register(name, strategy_class, dependencies)
        if dependencies:
            self._graph.add_dependencies(name, dependencies)

    async def execute(self, content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute all registered strategies.

        Args:
            content: Content to process
            metadata: Optional metadata to pass to strategies

        Returns:
            Dictionary mapping strategy names to their results
        """
        strategies = self._factory.get_strategies()
        return await self._pipeline.execute(strategies, content, metadata)

    def get_result(self, strategy_name: str) -> Optional[Any]:
        """Get the result of a previously executed strategy.

        Args:
            strategy_name: Name of the strategy

        Returns:
            Strategy result if available, None otherwise
        """
        return self._pipeline.get_result(strategy_name)

    def clear(self) -> None:
        """Clear all registered strategies and results."""
        self._factory.clear()
        self._graph.clear()
        self._pipeline.clear_cache()


__all__ = [
    # Legacy exports
    "StrategyManager",
    "TokenizationStrategy",
    "NERStrategy",
    "SentimentStrategy",
    "TopicStrategy",
    # Modern components
    "ModernStrategyManager",
    "StrategyFactory",
    "DependencyGraph",
    "StrategyPipeline",
    "ErrorHandler",
    "StrategyExecutionError",
]
