"""Validation framework.

This package provides a comprehensive validation framework for ensuring data
integrity and consistency across the system.
"""

from .base import CompositeValidator, ValidationError, ValidationStrategy, Validator
from .strategies import (
    BatchValidationParams,
    BatchValidator,
    ContentValidationParams,
    ContentValidator,
    MetadataValidationParams,
    MetadataValidator,
)
from .utils import (
    validate_length,
    validate_metadata_structure,
    validate_range,
    validate_type,
    validate_with_predicate,
)

__all__ = [
    # Base classes and protocols
    "Validator",
    "ValidationStrategy",
    "CompositeValidator",
    "ValidationError",
    # Validation strategies
    "ContentValidator",
    "ContentValidationParams",
    "BatchValidator",
    "BatchValidationParams",
    "MetadataValidator",
    "MetadataValidationParams",
    # Utility functions
    "validate_type",
    "validate_length",
    "validate_range",
    "validate_with_predicate",
    "validate_metadata_structure",
]
