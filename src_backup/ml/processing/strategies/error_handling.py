"""Error handling for strategy execution."""

import logging

from src.core.errors import ServiceInitializationError, ValidationError


class StrategyExecutionError(Exception):
    """Error raised when a strategy fails to execute."""

    def __init__(self, message: str, strategy_name: str):
        """Initialize the error.

        Args:
            message: Error message
            strategy_name: Name of the failed strategy
        """
        super().__init__(message)
        self.strategy_name = strategy_name


class ErrorHandler:
    """Centralized error handling for strategy execution.

    This class provides consistent error handling and logging for
    strategy-related errors, including dependency and execution failures.

    Attributes:
        _logger: Logger instance for error reporting
        _dependency_graph: Optional reference to strategy dependencies
    """

    def __init__(self, dependency_graph: dict[str, set[str]] | None = None) -> None:
        """Initialize the error handler.

        Args:
            dependency_graph: Optional mapping of strategy dependencies
        """
        self._logger = logging.getLogger(__name__)
        self._dependency_graph = dependency_graph

    def handle(self, error: Exception, strategy_name: str | None = None) -> None:
        """Handle strategy execution errors.

        Args:
            error: The error that occurred
            strategy_name: Optional name of the failed strategy
        """
        if isinstance(error, StrategyExecutionError):
            self._handle_strategy_error(error)
        elif isinstance(error, ServiceInitializationError):
            self._handle_initialization_error(error)
        elif isinstance(error, ValidationError):
            self._handle_validation_error(error, strategy_name)
        else:
            self._handle_general_error(error, strategy_name)

    def _handle_strategy_error(self, error: StrategyExecutionError) -> None:
        """Handle strategy-specific execution errors.

        Args:
            error: The strategy execution error
        """
        self._logger.error(
            "Strategy execution failed: %s (strategy: %s)",
            str(error),
            error.strategy_name,
        )

        # Check for affected dependent strategies
        if self._dependency_graph and error.strategy_name in self._dependency_graph:
            dependents = self._dependency_graph[error.strategy_name]
            if dependents:
                self._logger.warning(
                    "Failure in %s may affect dependent strategies: %s",
                    error.strategy_name,
                    ", ".join(dependents),
                )

    def _handle_initialization_error(self, error: ServiceInitializationError) -> None:
        """Handle service initialization errors.

        Args:
            error: The initialization error
        """
        self._logger.error(
            "Service initialization failed: %s (service: %s)",
            str(error),
            error.service_name,
        )

    def _handle_validation_error(
        self, error: ValidationError, strategy_name: str | None
    ) -> None:
        """Handle validation errors.

        Args:
            error: The validation error
            strategy_name: Optional name of the strategy that failed validation
        """
        context = f" in {strategy_name}" if strategy_name else ""
        self._logger.error("Validation failed%s: %s", context, str(error))

    def _handle_general_error(self, error: Exception, strategy_name: str | None) -> None:
        """Handle general execution errors.

        Args:
            error: The general error
            strategy_name: Optional name of the affected strategy
        """
        context = f" in {strategy_name}" if strategy_name else ""
        self._logger.error(
            "Unexpected error%s: %s (%s)",
            context,
            str(error),
            error.__class__.__name__,
        )

    def set_dependency_graph(self, graph: dict[str, set[str]]) -> None:
        """Update the dependency graph reference.

        Args:
            graph: New dependency graph mapping
        """
        self._dependency_graph = graph
