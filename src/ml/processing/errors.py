"""Custom exceptions for the processing package."""

from typing import Any, Optional

from src.core.errors import ProcessingError, ServiceStateError, ValidationError


class StrategyError(ProcessingError):
    """Raised when a processing strategy fails.

    This error indicates that a specific processing strategy
    encountered an error during execution.

    Attributes:
        message: Detailed error message
        strategy_name: Name of the failed strategy
        input_metadata: Input metadata that caused the failure
        error_context: Additional context about the failure
    """

    def __init__(
        self,
        message: str,
        strategy_name: Optional[str] = None,
        input_metadata: Optional[dict[str, Any]] = None,
        error_context: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Detailed error message
            strategy_name: Name of the failed strategy
            input_metadata: Input metadata that caused the failure
            error_context: Additional context about the failure
        """
        self.strategy_name = strategy_name
        self.input_metadata = input_metadata or {}
        self.error_context = error_context or {}
        super().__init__(message, metadata=error_context)


# Re-export common errors for backward compatibility
__all__ = [
    "ProcessingError",
    "ServiceStateError",
    "StrategyError",
    "ValidationError",
]
