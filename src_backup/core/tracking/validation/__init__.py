"""Document lineage validation package.

This module provides validation functionality for document lineage data, including:
- Validation strategies for different aspects of document lineage
- Error types and factories for validation errors
- Composite validator for executing multiple validation strategies
"""

from src.core.tracking.validation.composite import CompositeValidator
from src.core.tracking.validation.interface import (
    CircularDependencyError,
    InconsistentRelationshipError,
    LineageValidationErrorFactory,
    MissingReferenceError,
    ValidationError,
    ValidationStrategy,
)
from src.core.tracking.validation.strategies.chunks import ChunkReferenceValidator
from src.core.tracking.validation.strategies.circular import CircularDependencyValidator
from src.core.tracking.validation.strategies.relationships import RelationshipValidator


__all__ = [
    # Core Interfaces
    "ValidationStrategy",
    "ValidationError",
    # Error Types
    "CircularDependencyError",
    "InconsistentRelationshipError",
    "MissingReferenceError",
    "LineageValidationErrorFactory",
    # Validation Strategies
    "CircularDependencyValidator",
    "ChunkReferenceValidator",
    "RelationshipValidator",
    # Composite Validator
    "CompositeValidator",
]
