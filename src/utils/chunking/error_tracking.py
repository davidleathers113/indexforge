"""Error tracking utilities for reference system.

This module provides tools for tracking, analyzing, and reporting errors
across the reference system operations.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
import time
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of errors in the reference system."""

    REFERENCE_VALIDATION = auto()  # Reference validation errors
    METADATA_VALIDATION = auto()  # Metadata validation errors
    CACHE_OPERATION = auto()  # Cache-related errors
    CLASSIFICATION = auto()  # Classification errors
    BATCH_OPERATION = auto()  # Batch processing errors


@dataclass
class ErrorEvent:
    """Details of an error event."""

    category: ErrorCategory
    error_type: str
    message: str
    timestamp: float
    context: Dict = field(default_factory=dict)


@dataclass
class ErrorStats:
    """Statistics for error tracking."""

    total_errors: int = 0
    error_counts: Dict[ErrorCategory, int] = field(default_factory=lambda: defaultdict(int))
    error_rates: Dict[ErrorCategory, float] = field(default_factory=dict)
    recent_errors: List[ErrorEvent] = field(default_factory=list)
    error_trends: Dict[Tuple[ErrorCategory, str], int] = field(
        default_factory=lambda: defaultdict(int)
    )


class ErrorTracker:
    """Tracks and analyzes errors in the reference system."""

    def __init__(self, max_recent_errors: int = 100, error_window_seconds: float = 3600):
        """Initialize error tracker.

        Args:
            max_recent_errors: Maximum number of recent errors to store
            error_window_seconds: Time window for error rate calculation in seconds
        """
        self.max_recent_errors = max_recent_errors
        self.error_window_seconds = error_window_seconds
        self.error_events: List[ErrorEvent] = []
        self.start_time = time.time()
        self.operation_counts: Dict[ErrorCategory, int] = defaultdict(int)

    def record_error(
        self,
        category: ErrorCategory,
        error_type: str,
        message: str,
        context: Optional[Dict] = None,
    ) -> None:
        """Record an error event.

        Args:
            category: Category of the error
            error_type: Type of error within category
            message: Error message
            context: Additional context for the error
        """
        event = ErrorEvent(
            category=category,
            error_type=error_type,
            message=message,
            timestamp=time.time(),
            context=context or {},
        )

        self.error_events.append(event)
        if len(self.error_events) > self.max_recent_errors:
            self.error_events.pop(0)

        logger.error(
            "Error in %s: %s - %s",
            category.name,
            error_type,
            message,
            extra={"error_context": context},
        )

    def record_operation(self, category: ErrorCategory) -> None:
        """Record an operation attempt for error rate calculation.

        Args:
            category: Category of operation
        """
        self.operation_counts[category] += 1

    def get_error_stats(self, window_seconds: Optional[float] = None) -> ErrorStats:
        """Get error statistics for the specified time window.

        Args:
            window_seconds: Time window in seconds, defaults to instance window

        Returns:
            Statistics about errors in the time window
        """
        window = window_seconds or self.error_window_seconds
        current_time = time.time()
        cutoff_time = current_time - window

        # Filter events in window
        recent_events = [event for event in self.error_events if event.timestamp >= cutoff_time]

        stats = ErrorStats()
        stats.total_errors = len(recent_events)
        stats.recent_errors = recent_events[-self.max_recent_errors :]

        # Calculate error counts and trends
        for event in recent_events:
            stats.error_counts[event.category] += 1
            stats.error_trends[(event.category, event.error_type)] += 1

        # Calculate error rates
        for category in ErrorCategory:
            operation_count = self.operation_counts[category]
            error_count = stats.error_counts[category]
            if operation_count > 0:
                stats.error_rates[category] = (error_count / operation_count) * 100
            else:
                stats.error_rates[category] = 0.0

        return stats

    def get_error_trends(
        self, num_periods: int = 6, period_seconds: float = 600
    ) -> Dict[ErrorCategory, List[int]]:
        """Get error count trends over time periods.

        Args:
            num_periods: Number of time periods to analyze
            period_seconds: Length of each period in seconds

        Returns:
            Dictionary mapping categories to lists of error counts per period
        """
        trends: Dict[ErrorCategory, List[int]] = {
            category: [0] * num_periods for category in ErrorCategory
        }

        current_time = time.time()
        for period in range(num_periods):
            start_time = current_time - (period + 1) * period_seconds
            end_time = current_time - period * period_seconds

            for event in self.error_events:
                if start_time <= event.timestamp < end_time:
                    trends[event.category][period] += 1

        return trends

    def get_frequent_errors(self, limit: int = 5) -> List[Tuple[Tuple[ErrorCategory, str], int]]:
        """Get most frequent error types.

        Args:
            limit: Maximum number of error types to return

        Returns:
            List of (category, error_type) tuples with their counts
        """
        error_counts: Dict[Tuple[ErrorCategory, str], int] = defaultdict(int)
        for event in self.error_events:
            error_counts[(event.category, event.error_type)] += 1

        return sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

    def get_error_summary(self) -> str:
        """Get a human-readable summary of error statistics.

        Returns:
            Formatted string with error summary
        """
        stats = self.get_error_stats()
        trends = self.get_error_trends()
        frequent_errors = self.get_frequent_errors()

        summary = [
            "Error Summary:",
            f"Total Errors: {stats.total_errors}",
            "\nError Rates by Category:",
        ]

        for category in ErrorCategory:
            rate = stats.error_rates.get(category, 0.0)
            count = stats.error_counts.get(category, 0)
            summary.append(
                f"- {category.name}: {rate:.2f}% ({count} errors / "
                f"{self.operation_counts[category]} operations)"
            )

        summary.append("\nMost Frequent Errors:")
        for (category, error_type), count in frequent_errors:
            summary.append(f"- {category.name} - {error_type}: {count} occurrences")

        summary.append("\nError Trends (most recent first):")
        for category, counts in trends.items():
            if sum(counts) > 0:
                summary.append(f"- {category.name}: {' -> '.join(map(str, reversed(counts)))}")

        return "\n".join(summary)

    def clear(self) -> None:
        """Clear all error tracking data."""
        self.error_events.clear()
        self.operation_counts.clear()
        self.start_time = time.time()


def track_errors(error_tracker: ErrorTracker, category: ErrorCategory):
    """Decorator to track errors in operations.

    Args:
        error_tracker: Error tracker to record errors
        category: Category of operation
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            error_tracker.record_operation(category)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_tracker.record_error(
                    category=category,
                    error_type=type(e).__name__,
                    message=str(e),
                    context={"args": args, "kwargs": kwargs},
                )
                raise

        return wrapper

    return decorator
