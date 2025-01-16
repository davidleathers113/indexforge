"""Base classes for fixtures."""

from dataclasses import dataclass, field


@dataclass
class BaseState:
    """Base state management for fixtures."""

    errors: list[str] = field(default_factory=list)

    def reset(self):
        """Reset state to defaults."""
        self.errors.clear()

    def add_error(self, error: str):
        """Add an error with logging."""
        self.errors.append(error)

    def get_errors(self) -> list[str]:
        """Get copy of current errors."""
        return self.errors.copy()
