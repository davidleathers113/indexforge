"""Performance analyzer implementation using the Strategy pattern."""

from typing import Any, Dict, List, Optional

from tests.performance.analysis.strategies import AnalysisStrategy


class PerformanceAnalyzer:
    """Executes performance analysis using configured strategies."""

    def __init__(self, strategies: Optional[List[AnalysisStrategy]] = None):
        """Initialize the analyzer with strategies.

        Args:
            strategies: List of analysis strategies to use
        """
        self.strategies = strategies or []

    def add_strategy(self, strategy: AnalysisStrategy) -> None:
        """Add an analysis strategy.

        Args:
            strategy: Strategy to add
        """
        self.strategies.append(strategy)

    def analyze(self, values: List[float], **kwargs) -> Dict[str, Any]:
        """Run all configured analysis strategies.

        Args:
            values: List of metric values to analyze
            **kwargs: Additional parameters passed to each strategy

        Returns:
            Combined analysis results from all strategies
        """
        if not values:
            return {}

        results = {}
        for strategy in self.strategies:
            try:
                strategy_name = strategy.__class__.__name__.lower().replace("analysis", "")
                results[strategy_name] = strategy.analyze(values, **kwargs)
            except Exception as e:
                results[f"{strategy_name}_error"] = str(e)

        return results


class PerformanceAnalysisBuilder:
    """Builder for configuring performance analysis."""

    def __init__(self):
        """Initialize the builder."""
        self.strategies: List[AnalysisStrategy] = []

    def add_strategy(self, strategy: AnalysisStrategy) -> "PerformanceAnalysisBuilder":
        """Add an analysis strategy.

        Args:
            strategy: Strategy to add

        Returns:
            Self for method chaining
        """
        self.strategies.append(strategy)
        return self

    def build(self) -> PerformanceAnalyzer:
        """Create a PerformanceAnalyzer with configured strategies.

        Returns:
            Configured analyzer instance
        """
        return PerformanceAnalyzer(self.strategies)
