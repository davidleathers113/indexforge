"""Validation interfaces for document lineage validation."""

from abc import ABC, abstractmethod
from typing import Protocol

from src.core.models import DocumentLineage


class ValidationStrategy(Protocol):
    """Protocol defining the contract for validation strategies."""

    def validate(self, lineage_data: dict[str, DocumentLineage]) -> list[str]:
        """Execute validation strategy and return list of error messages."""
        ...


class ValidationError(Protocol):
    """Protocol for validation error creation."""

    def format_message(self) -> str:
        """Format the error message."""
        ...


class ValidationErrorFactory(ABC):
    """Abstract factory for creating validation errors."""

    @abstractmethod
    def create_error(self, error_type: str, **kwargs) -> ValidationError:
        """Create a validation error of the specified type."""
        ...
