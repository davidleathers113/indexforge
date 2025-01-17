"""Core tracking functionality for IndexForge.

This module provides core tracking functionality including:
- Document lineage tracking and validation
- Processing status tracking
- Health status monitoring
- Reference type management
- Transformation tracking
- Source configuration and tracking
"""

from .enums import HealthStatus, LogLevel, ProcessingStatus, ReferenceType, TransformationType
from .source import SourceConfig, SourceTracker, TenantSourceTracker
from .validation import (
    ChunkReferenceValidator,
    CircularDependencyValidator,
    CompositeValidator,
    RelationshipValidator,
    ValidationError,
    ValidationStrategy,
)


__all__ = [
    # Enums
    "HealthStatus",
    "LogLevel",
    "ProcessingStatus",
    "ReferenceType",
    "TransformationType",
    # Source tracking
    "SourceConfig",
    "SourceTracker",
    "TenantSourceTracker",
    # Validation
    "ChunkReferenceValidator",
    "CircularDependencyValidator",
    "CompositeValidator",
    "RelationshipValidator",
    "ValidationError",
    "ValidationStrategy",
]
