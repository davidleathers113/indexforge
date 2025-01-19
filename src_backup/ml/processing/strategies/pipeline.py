"""Pipeline for executing processing strategies."""

from typing import Any

from src.ml.processing.models.strategies import ProcessingStrategy

from .dependency import DependencyGraph
from .error_handling import ErrorHandler, StrategyExecutionError


class StrategyPipeline:
    """Executes strategies in dependency order.

    This class manages the execution of processing strategies while respecting
    their dependencies and handling errors appropriately.

    Attributes:
        _graph: Dependency graph for determining execution order
        _error_handler: Handler for execution errors
        _results_cache: Cache of strategy execution results
    """

    def __init__(self, dependency_graph: DependencyGraph):
        """Initialize the strategy pipeline.

        Args:
            dependency_graph: Graph of strategy dependencies
        """
        self._graph = dependency_graph
        self._error_handler = ErrorHandler(self._graph._forward_deps)
        self._results_cache: dict[str, Any] = {}

    async def execute(
        self,
        strategies: dict[str, ProcessingStrategy],
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute strategies in dependency order.

        Args:
            strategies: Dictionary mapping strategy names to instances
            content: Content to process
            metadata: Optional metadata to pass to strategies

        Returns:
            Dictionary mapping strategy names to their results

        Raises:
            StrategyExecutionError: If any strategy fails to execute
        """
        self._results_cache.clear()
        execution_metadata = metadata.copy() if metadata else {}

        try:
            # Get optimized execution order
            execution_order = self._graph.get_execution_order()

            # Execute strategies in order
            for strategy_name in execution_order:
                if strategy_name not in strategies:
                    continue

                strategy = strategies[strategy_name]
                result = await self._execute_strategy(
                    strategy_name, strategy, content, execution_metadata
                )
                self._results_cache[strategy_name] = result

                # Update metadata with strategy results
                if hasattr(result, "metadata"):
                    execution_metadata.update(result.metadata)

        except Exception as e:
            self._error_handler.handle(e)
            raise

        return self._results_cache

    async def _execute_strategy(
        self, name: str, strategy: ProcessingStrategy, content: str, metadata: dict[str, Any]
    ) -> Any:
        """Execute a single strategy.

        Args:
            name: Name of the strategy
            strategy: Strategy instance to execute
            content: Content to process
            metadata: Current execution metadata

        Returns:
            Strategy execution result

        Raises:
            StrategyExecutionError: If strategy execution fails
        """
        try:
            # Validate input
            validation_errors = strategy.validate(content)
            if validation_errors:
                raise StrategyExecutionError(
                    f"Validation failed: {validation_errors}",
                    strategy_name=name,
                )

            # Execute strategy
            result = strategy.process(content, metadata)

            # Validate result
            if hasattr(result, "validate"):
                result_errors = result.validate()
                if result_errors:
                    raise StrategyExecutionError(
                        f"Result validation failed: {result_errors}",
                        strategy_name=name,
                    )

            return result

        except Exception as e:
            if not isinstance(e, StrategyExecutionError):
                e = StrategyExecutionError(str(e), strategy_name=name)
            raise e

    def get_result(self, strategy_name: str) -> Any | None:
        """Get the result of a previously executed strategy.

        Args:
            strategy_name: Name of the strategy

        Returns:
            Strategy result if available, None otherwise
        """
        return self._results_cache.get(strategy_name)

    def clear_cache(self) -> None:
        """Clear the results cache."""
        self._results_cache.clear()
