"""Validation error types and factory implementations."""

from dataclasses import dataclass
from typing import Any

from .interfaces import ValidationError, ValidationErrorFactory


@dataclass
class CircularDependencyError(ValidationError):
    """Error for circular dependency detection."""

    cycle: list[str]

    def format_message(self) -> str:
        """Format the circular dependency error message."""
        return f"Circular derivation detected: {' -> '.join(self.cycle)}"


@dataclass
class MissingReferenceError(ValidationError):
    """Error for missing document references."""

    source_id: str
    target_id: str
    reference_type: str

    def format_message(self) -> str:
        """Format the missing reference error message."""
        return f"Document {self.source_id} references nonexistent {self.reference_type} document {self.target_id}"


@dataclass
class InconsistentRelationshipError(ValidationError):
    """Error for inconsistent relationships between documents."""

    source_id: str
    target_id: str
    relationship_type: str
    details: str

    def format_message(self) -> str:
        """Format the inconsistent relationship error message."""
        return (
            f"Inconsistent {self.relationship_type} relationship: {self.source_id} {self.details} "
            f"{self.target_id}"
        )


class LineageValidationErrorFactory(ValidationErrorFactory):
    """Factory for creating lineage validation errors."""

    ERROR_TYPES = {
        "circular": CircularDependencyError,
        "missing": MissingReferenceError,
        "inconsistent": InconsistentRelationshipError,
    }

    def create_error(self, error_type: str, **kwargs: Any) -> ValidationError:
        """Create a validation error of the specified type."""
        if error_type not in self.ERROR_TYPES:
            raise ValueError(f"Unknown error type: {error_type}")

        error_class = self.ERROR_TYPES[error_type]
        return error_class(**kwargs)
