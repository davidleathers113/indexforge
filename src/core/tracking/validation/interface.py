"""Interfaces for document lineage validation strategies.

This module defines the core interfaces and protocols for implementing
validation strategies in the document lineage system. It provides a flexible
framework for adding new validation rules while maintaining consistency
across different types of validation.

Key Features:
    - ValidationStrategy protocol for implementing validation rules
    - ValidationError protocol for standardized error reporting
    - Factory class for creating validation errors
    - Common validation error types
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from src.core.models import DocumentLineage


@runtime_checkable
class ValidationStrategy(Protocol):
    """Protocol for implementing document lineage validation strategies."""

    def validate(self, lineage_data: dict[str, DocumentLineage]) -> list[str]:
        """Validate document lineage data according to strategy rules.

        Args:
            lineage_data: Dictionary mapping document IDs to their lineage data

        Returns:
            List of validation error messages
        """
        ...


@dataclass
class ValidationError:
    """Base class for validation errors."""

    message: str

    def format_error(self) -> str:
        """Format the error message for display."""
        return self.message


@dataclass
class CircularDependencyError(ValidationError):
    """Error indicating a circular dependency in document lineage."""

    cycle: list[str]

    def format_error(self) -> str:
        """Format the circular dependency error message."""
        cycle_str = " -> ".join(self.cycle)
        return f"{self.message}: {cycle_str}"


@dataclass
class MissingReferenceError(ValidationError):
    """Error indicating a missing document reference."""

    source_id: str
    target_id: str

    def format_error(self) -> str:
        """Format the missing reference error message."""
        return f"{self.message} (Source: {self.source_id}, Target: {self.target_id})"


@dataclass
class InconsistentRelationshipError(ValidationError):
    """Error indicating inconsistent relationships between documents."""

    doc_id: str
    related_id: str
    relationship_type: str

    def format_error(self) -> str:
        """Format the inconsistent relationship error message."""
        return (
            f"{self.message} (Document: {self.doc_id}, Related: {self.related_id}, "
            f"Type: {self.relationship_type})"
        )


class LineageValidationErrorFactory:
    """Factory class for creating validation errors."""

    @staticmethod
    def create_circular_dependency_error(cycle: list[str]) -> CircularDependencyError:
        """Create a circular dependency error."""
        return CircularDependencyError(
            message="Circular dependency detected in document lineage", cycle=cycle
        )

    @staticmethod
    def create_missing_reference_error(
        source_id: str, target_id: str, context: str
    ) -> MissingReferenceError:
        """Create a missing reference error."""
        return MissingReferenceError(
            message=f"Missing {context} reference", source_id=source_id, target_id=target_id
        )

    @staticmethod
    def create_inconsistent_relationship_error(
        doc_id: str, related_id: str, relationship_type: str
    ) -> InconsistentRelationshipError:
        """Create an inconsistent relationship error."""
        return InconsistentRelationshipError(
            message="Inconsistent document relationship detected",
            doc_id=doc_id,
            related_id=related_id,
            relationship_type=relationship_type,
        )
