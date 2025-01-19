"""Reference caching implementation for optimizing reference access.

This module provides caching functionality for frequently accessed references,
including cache invalidation strategies and memory optimization.
"""

from collections import OrderedDict
from dataclasses import dataclass
from typing import TypeVar
from uuid import UUID

from .references import Reference, ReferenceManager


T = TypeVar("T")


class LRUCache(OrderedDict):
    """LRU cache implementation with size limit."""

    def __init__(self, maxsize: int = 1000):
        """Initialize LRU cache with maximum size.

        Args:
            maxsize: Maximum number of items to store in cache
        """
        super().__init__()
        self.maxsize = maxsize

    def get(self, key: T) -> T | None:
        """Get item from cache and move to end if exists.

        Args:
            key: Cache key to retrieve

        Returns:
            Cached value if exists, None otherwise
        """
        if key not in self:
            return None
        self.move_to_end(key)
        return self[key]

    def put(self, key: T, value: T) -> None:
        """Add item to cache, removing oldest if at capacity.

        Args:
            key: Cache key
            value: Value to cache
        """
        if key in self:
            self.move_to_end(key)
        self[key] = value
        if len(self) > self.maxsize:
            self.popitem(last=False)


@dataclass
class CacheStats:
    """Statistics for cache performance monitoring."""

    hits: int = 0
    misses: int = 0
    invalidations: int = 0

    @property
    def total_requests(self) -> int:
        """Total number of cache requests."""
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        """Cache hit rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100


class ReferenceCache:
    """Cache manager for frequently accessed references."""

    def __init__(self, ref_manager: ReferenceManager, maxsize: int = 1000):
        """Initialize reference cache.

        Args:
            ref_manager: Reference manager to cache references for
            maxsize: Maximum number of references to cache
        """
        self.ref_manager = ref_manager
        self.reference_cache = LRUCache(maxsize=maxsize)
        self.forward_index: dict[UUID, set[UUID]] = {}  # source -> targets
        self.reverse_index: dict[UUID, set[UUID]] = {}  # target -> sources
        self.stats = CacheStats()

    def get_reference(self, source_id: UUID, target_id: UUID) -> Reference | None:
        """Get reference from cache if available, falling back to manager.

        Args:
            source_id: Source chunk ID
            target_id: Target chunk ID

        Returns:
            Cached reference if exists, None otherwise
        """
        cache_key = (source_id, target_id)
        cached_ref = self.reference_cache.get(cache_key)

        if cached_ref is not None:
            self.stats.hits += 1
            return cached_ref

        self.stats.misses += 1
        ref = self.ref_manager._references.get(cache_key)
        if ref is not None:
            self.cache_reference(source_id, target_id, ref)
        return ref

    def cache_reference(self, source_id: UUID, target_id: UUID, ref: Reference) -> None:
        """Add reference to cache and update indices.

        Args:
            source_id: Source chunk ID
            target_id: Target chunk ID
            ref: Reference to cache
        """
        cache_key = (source_id, target_id)
        self.reference_cache.put(cache_key, ref)

        # Update forward index
        if source_id not in self.forward_index:
            self.forward_index[source_id] = set()
        self.forward_index[source_id].add(target_id)

        # Update reverse index
        if target_id not in self.reverse_index:
            self.reverse_index[target_id] = set()
        self.reverse_index[target_id].add(source_id)

        # Cache reverse reference if bidirectional
        if ref.bidirectional:
            reverse_key = (target_id, source_id)
            reverse_ref = self.ref_manager._references.get(reverse_key)
            if reverse_ref is not None:
                self.reference_cache.put(reverse_key, reverse_ref)

    def invalidate_reference(self, source_id: UUID, target_id: UUID) -> None:
        """Remove reference from cache.

        Args:
            source_id: Source chunk ID
            target_id: Target chunk ID
        """
        cache_key = (source_id, target_id)
        if cache_key in self.reference_cache:
            del self.reference_cache[cache_key]
            self.stats.invalidations += 1

        # Update indices
        if source_id in self.forward_index:
            self.forward_index[source_id].discard(target_id)
        if target_id in self.reverse_index:
            self.reverse_index[target_id].discard(source_id)

    def invalidate_chunk_references(self, chunk_id: UUID) -> None:
        """Invalidate all references involving a chunk.

        Args:
            chunk_id: ID of chunk whose references to invalidate
        """
        # Invalidate forward references
        if chunk_id in self.forward_index:
            for target_id in self.forward_index[chunk_id]:
                self.invalidate_reference(chunk_id, target_id)
            del self.forward_index[chunk_id]

        # Invalidate reverse references
        if chunk_id in self.reverse_index:
            for source_id in self.reverse_index[chunk_id]:
                self.invalidate_reference(source_id, chunk_id)
            del self.reverse_index[chunk_id]

    def get_chunk_references(self, chunk_id: UUID) -> dict[UUID, Reference]:
        """Get all references involving a chunk.

        Args:
            chunk_id: Chunk ID to get references for

        Returns:
            Dictionary mapping target IDs to references
        """
        references = {}

        # Get forward references
        if chunk_id in self.forward_index:
            for target_id in self.forward_index[chunk_id]:
                ref = self.get_reference(chunk_id, target_id)
                if ref is not None:
                    references[target_id] = ref

        # Get reverse references
        if chunk_id in self.reverse_index:
            for source_id in self.reverse_index[chunk_id]:
                ref = self.get_reference(source_id, chunk_id)
                if ref is not None:
                    references[source_id] = ref

        return references

    def clear(self) -> None:
        """Clear all cached references and indices."""
        self.reference_cache.clear()
        self.forward_index.clear()
        self.reverse_index.clear()
        self.stats = CacheStats()

    def get_stats(self) -> CacheStats:
        """Get current cache statistics.

        Returns:
            Cache statistics including hits, misses, and invalidations
        """
        return self.stats
