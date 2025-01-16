"""Factory for creating and configuring processing strategies."""

from typing import Dict, Optional, Set, Type

from src.core.errors import ServiceInitializationError
from src.ml.processing.models.strategies import ProcessingStrategy


class StrategyFactory:
    """Factory for creating and configuring processing strategies.

    This class manages the registration and instantiation of processing strategies,
    ensuring type safety and proper initialization.

    Attributes:
        _registry: Mapping of strategy names to their implementing classes
        _instances: Cache of instantiated strategy instances
        _dependencies: Strategy dependency requirements
    """

    def __init__(self) -> None:
        """Initialize the strategy factory."""
        self._registry: Dict[str, Type[ProcessingStrategy]] = {}
        self._instances: Dict[str, ProcessingStrategy] = {}
        self._dependencies: Dict[str, Set[str]] = {
            "TokenizationStrategy": set(),  # No dependencies
            "NERStrategy": {"TokenizationStrategy"},  # Requires tokenization
            "SentimentStrategy": {"TokenizationStrategy"},  # Requires tokenization
            "TopicStrategy": set(),  # Independent
            "SummaryStrategy": {"TokenizationStrategy"},  # Requires tokenization
            "KeywordStrategy": {"TokenizationStrategy"},  # Requires tokenization
        }

    def register(
        self,
        name: str,
        strategy_class: Type[ProcessingStrategy],
        dependencies: Optional[Set[str]] = None,
    ) -> None:
        """Register a strategy class.

        Args:
            name: Name of the strategy
            strategy_class: Strategy class to register
            dependencies: Optional set of strategy dependencies

        Raises:
            ValueError: If strategy name is already registered
            TypeError: If strategy_class doesn't implement ProcessingStrategy
        """
        if name in self._registry:
            raise ValueError(f"Strategy {name} is already registered")

        # Verify the class implements ProcessingStrategy
        if not hasattr(strategy_class, "process") or not hasattr(strategy_class, "validate"):
            raise TypeError(
                f"Strategy class {strategy_class.__name__} must implement ProcessingStrategy protocol"
            )

        self._registry[name] = strategy_class
        if dependencies is not None:
            self._dependencies[name] = dependencies

    def create(self, name: str, **kwargs) -> ProcessingStrategy:
        """Create a strategy instance.

        Args:
            name: Name of the strategy to create
            **kwargs: Additional arguments to pass to strategy constructor

        Returns:
            Instantiated strategy

        Raises:
            ValueError: If strategy is not registered
            ServiceInitializationError: If strategy initialization fails
        """
        if name not in self._registry:
            raise ValueError(f"Strategy {name} is not registered")

        # Return cached instance if available
        if name in self._instances:
            return self._instances[name]

        try:
            strategy = self._registry[name](**kwargs)
            self._instances[name] = strategy
            return strategy
        except Exception as e:
            raise ServiceInitializationError(
                f"Failed to initialize strategy {name}: {str(e)}",
                service_name=name,
            ) from e

    def get_dependencies(self, name: str) -> Set[str]:
        """Get dependencies for a strategy.

        Args:
            name: Name of the strategy

        Returns:
            Set of dependency strategy names

        Raises:
            ValueError: If strategy is not registered
        """
        if name not in self._registry:
            raise ValueError(f"Strategy {name} is not registered")

        return self._dependencies.get(name, set())

    def get_strategies(self) -> Dict[str, ProcessingStrategy]:
        """Get all registered strategy instances.

        Returns:
            Dictionary mapping strategy names to instances
        """
        # Create any uncreated instances
        for name in self._registry:
            if name not in self._instances:
                self.create(name)

        return self._instances

    def clear(self) -> None:
        """Clear all registered strategies and instances."""
        self._registry.clear()
        self._instances.clear()
        self._dependencies.clear()
