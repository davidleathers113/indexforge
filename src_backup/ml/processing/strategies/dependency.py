"""Dependency management for processing strategies."""

from collections import defaultdict

from src.core.errors import ServiceInitializationError


class DependencyGraph:
    """Manages strategy dependencies and execution ordering.

    This class handles the relationships between strategies and determines
    the optimal execution order based on dependencies.

    Attributes:
        _forward_deps: Direct dependencies for each strategy
        _reverse_deps: Reverse dependencies (what depends on each strategy)
    """

    def __init__(self) -> None:
        """Initialize the dependency graph."""
        self._forward_deps: dict[str, set[str]] = defaultdict(set)
        self._reverse_deps: dict[str, set[str]] = defaultdict(set)

    def add_dependency(self, strategy: str, depends_on: str) -> None:
        """Add a dependency relationship.

        Args:
            strategy: Name of the dependent strategy
            depends_on: Name of the strategy being depended on

        Raises:
            ServiceInitializationError: If adding would create a circular dependency
        """
        # Check for circular dependency before adding
        if self._would_create_cycle(strategy, depends_on):
            raise ServiceInitializationError(
                f"Adding dependency from {strategy} to {depends_on} would create a cycle",
                service_name=strategy,
            )

        self._forward_deps[strategy].add(depends_on)
        self._reverse_deps[depends_on].add(strategy)

    def add_dependencies(self, strategy: str, dependencies: set[str]) -> None:
        """Add multiple dependencies for a strategy.

        Args:
            strategy: Name of the dependent strategy
            dependencies: Set of strategy names being depended on

        Raises:
            ServiceInitializationError: If adding would create a circular dependency
        """
        for dep in dependencies:
            self.add_dependency(strategy, dep)

    def get_dependencies(self, strategy: str) -> set[str]:
        """Get direct dependencies for a strategy.

        Args:
            strategy: Name of the strategy

        Returns:
            Set of dependency names
        """
        return self._forward_deps[strategy]

    def get_dependents(self, strategy: str) -> set[str]:
        """Get strategies that depend on the given strategy.

        Args:
            strategy: Name of the strategy

        Returns:
            Set of dependent strategy names
        """
        return self._reverse_deps[strategy]

    def get_execution_order(self) -> list[str]:
        """Get optimized execution order respecting dependencies.

        Returns:
            List of strategy names in execution order

        Raises:
            ServiceInitializationError: If dependencies contain a cycle
        """
        # Kahn's algorithm for topological sort
        in_degree: dict[str, int] = defaultdict(int)
        for strategy in self._forward_deps:
            for dep in self._forward_deps[strategy]:
                in_degree[dep] += 1

        # Start with nodes that have no dependencies
        ready: list[str] = [node for node in self._forward_deps if in_degree[node] == 0]

        result = []
        while ready:
            node = ready.pop(0)
            result.append(node)

            # Update in-degrees and find newly ready nodes
            for dependent in self._reverse_deps[node]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    ready.append(dependent)

        # Check for cycles
        if len(result) != len(self._forward_deps):
            raise ServiceInitializationError(
                "Dependency graph contains cycles",
                service_name="DependencyGraph",
            )

        return result

    def _would_create_cycle(self, strategy: str, depends_on: str) -> bool:
        """Check if adding a dependency would create a cycle.

        Args:
            strategy: Strategy to add dependency to
            depends_on: Strategy being depended on

        Returns:
            True if adding the dependency would create a cycle
        """
        if strategy == depends_on:
            return True

        # Check if depends_on depends on strategy (would create cycle)
        visited = set()

        def has_path(start: str, target: str) -> bool:
            if start == target:
                return True
            if start in visited:
                return False

            visited.add(start)
            for dep in self._forward_deps[start]:
                if has_path(dep, target):
                    return True
            visited.remove(start)
            return False

        return has_path(depends_on, strategy)

    def clear(self) -> None:
        """Clear all dependency relationships."""
        self._forward_deps.clear()
        self._reverse_deps.clear()
