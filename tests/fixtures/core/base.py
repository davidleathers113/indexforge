"""Base classes for fixtures."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class BaseState:
    """Base state management for fixtures."""

    errors: List[str] = field(default_factory=list)

    def reset(self):
        """Reset state to defaults."""
        self.errors.clear()

    def add_error(self, error: str):
        """Add an error with logging."""
        self.errors.append(error)

    def get_errors(self) -> List[str]:
        """Get copy of current errors."""
        return self.errors.copy()
