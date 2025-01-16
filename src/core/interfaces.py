"""DEPRECATED: Core interfaces.

This module is deprecated. Use the interfaces from src.core.interfaces.* instead.
This module now re-exports the Protocol-based interfaces for backward compatibility.

Migration Guide:
1. Update imports to use specific interfaces:
   from src.core.interfaces.processing import ChunkEmbedder
   from src.core.interfaces.storage import StorageMetrics
   from src.core.interfaces.reference import ReferenceManager
   etc.

2. Update implementations to match the new Protocol interfaces:
   - Add metadata support
   - Implement proper error handling
   - Add validation methods
   - Use specific type hints

This module will be removed in a future version.
"""

from __future__ import annotations

from typing import TypeVar
import warnings

# Re-export Protocol interfaces
from .interfaces.processing import (
    ChunkEmbedder,
    ChunkProcessor,
    ChunkTransformer,
    ChunkValidator,
    TextProcessor,
)
from .interfaces.reference import ReferenceManager, ReferenceValidator, SemanticReferenceManager
from .interfaces.search import VectorSearcher
from .interfaces.storage import ChunkStorage, DocumentStorage, ReferenceStorage, StorageMetrics


# Type variables for backward compatibility
T = TypeVar("T")  # Document type
C = TypeVar("C")  # Chunk type
R = TypeVar("R")  # Reference type

warnings.warn(
    "src.core.interfaces is deprecated. Use src.core.interfaces.* instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    # Re-exported interfaces
    "ChunkEmbedder",
    "ChunkProcessor",
    "ChunkTransformer",
    "ChunkValidator",
    "TextProcessor",
    "StorageMetrics",
    "DocumentStorage",
    "ChunkStorage",
    "ReferenceStorage",
    "ReferenceManager",
    "ReferenceValidator",
    "SemanticReferenceManager",
    "VectorSearcher",
    # Type variables
    "T",
    "C",
    "R",
]
