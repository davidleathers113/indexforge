"""Strategy registry for text processing.

This module provides a registry for managing and accessing text processing
strategies, ensuring proper initialization and dependency management.
"""

import logging
from typing import Any, Dict, List, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class ProcessingStrategy(Protocol):
    """Protocol defining the interface for processing strategies."""

    def process(self, content: str, metadata: Dict[str, Any] | None = None) -> Any:
        """Process text content.

        Args:
            content: Text content to process
            metadata: Optional processing metadata

        Returns:
            Processing results
        """
        ...

    def validate_dependencies(self) -> List[str]:
        """Validate strategy dependencies.

        Returns:
            List of missing dependencies
        """
        ...


class StrategyRegistry:
    """Registry for managing processing strategies.

    This class provides centralized management of processing strategies,
    including registration, validation, and access.
    """

    def __init__(self) -> None:
        """Initialize the strategy registry."""
        self._strategies: Dict[str, ProcessingStrategy] = {}
        self._initialized = False

    def register(self, name: str, strategy: ProcessingStrategy) -> None:
        """Register a processing strategy.

        Args:
            name: Strategy name
            strategy: Strategy instance

        Raises:
            ValueError: If strategy name already exists
            TypeError: If strategy doesn't implement ProcessingStrategy
        """
        if name in self._strategies:
            raise ValueError(f"Strategy already registered: {name}")

        if not isinstance(strategy, ProcessingStrategy):
            raise TypeError("Strategy must implement ProcessingStrategy protocol")

        self._strategies[name] = strategy
        logger.info(f"Registered strategy: {name}")

    def get_strategy(self, name: str) -> ProcessingStrategy:
        """Get a registered strategy.

        Args:
            name: Strategy name

        Returns:
            Strategy instance

        Raises:
            KeyError: If strategy not found
        """
        if name not in self._strategies:
            raise KeyError(f"Strategy not found: {name}")
        return self._strategies[name]

    def validate_dependencies(self) -> List[str]:
        """Validate dependencies for all registered strategies.

        Returns:
            List of missing dependencies
        """
        missing_deps = []
        for name, strategy in self._strategies.items():
            deps = strategy.validate_dependencies()
            if deps:
                missing_deps.extend(deps)
                logger.warning(f"Strategy {name} missing dependencies: {deps}")
        return list(set(missing_deps))  # Remove duplicates

    @property
    def strategies(self) -> Dict[str, ProcessingStrategy]:
        """Get all registered strategies.

        Returns:
            Dictionary of strategy names to instances
        """
        return self._strategies.copy()

    def clear(self) -> None:
        """Clear all registered strategies."""
        self._strategies.clear()
        logger.info("Cleared all strategies")
