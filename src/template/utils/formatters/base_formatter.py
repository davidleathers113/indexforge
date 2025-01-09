"""Base formatter class."""

from abc import ABC, abstractmethod


class BaseFormatter(ABC):
    """Base class for all code formatters."""

    @abstractmethod
    def format(self, content: str) -> str:
        """Format the given content.

        Args:
            content: Content to format

        Returns:
            str: Formatted content
        """
        pass
