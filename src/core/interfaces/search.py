"""Search interfaces.

This module provides interfaces for vector-based search operations and
semantic similarity matching.
"""

from __future__ import annotations

from .semantic import SearchStrategy, VectorSearcher
from .vector import (
    AddObjectCommand,
    BatchAddCommand,
    BatchDeleteCommand,
    DeleteObjectCommand,
    GetObjectCommand,
    VectorCommand,
    VectorSearchCommand,
    VectorService,
)

__all__ = [
    "AddObjectCommand",
    "BatchAddCommand",
    "BatchDeleteCommand",
    "DeleteObjectCommand",
    "GetObjectCommand",
    "SearchStrategy",
    "VectorCommand",
    "VectorSearchCommand",
    "VectorSearcher",
    "VectorService",
]
