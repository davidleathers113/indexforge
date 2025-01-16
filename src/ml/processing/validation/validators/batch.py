"""Batch validation strategies with optimized processing."""

from typing import Dict, List, Optional, Set

from src.ml.processing.models.chunks import Chunk, ChunkBatch
from src.ml.processing.validation.validators.base import ValidationStrategy


class BatchValidator(ValidationStrategy):
    """Validates consistency across batches of chunks with optimized processing."""

    def __init__(
        self,
        max_batch_size: int = 1000,
        max_memory_mb: int = 500,
        chunk_processing_timeout: float = 30.0,
    ) -> None:
        """Initialize batch validator with resource constraints.

        Args:
            max_batch_size: Maximum number of chunks in a batch
            max_memory_mb: Maximum memory usage in MB
            chunk_processing_timeout: Timeout per chunk in seconds
        """
        self.max_batch_size = max_batch_size
        self._max_memory_bytes = max_memory_mb * 1024 * 1024
        self._chunk_timeout = chunk_processing_timeout
        self._metadata_cache: Dict[str, Set[str]] = {}

    def _estimate_memory_usage(self, batch: ChunkBatch) -> int:
        """Estimate memory usage for a batch.

        Args:
            batch: Batch to estimate memory for

        Returns:
            int: Estimated memory usage in bytes
        """
        # Basic estimation - can be refined based on actual profiling
        return sum(
            (
                len(chunk.content.encode())
                + sum(len(str(v).encode()) for v in chunk.metadata.values())
                if chunk.metadata
                else len(chunk.content.encode())
            )
            for chunk in batch.chunks
        )

    def _validate_metadata_consistency(self, chunk: Chunk, batch: ChunkBatch) -> List[str]:
        """Validate metadata consistency efficiently.

        Args:
            chunk: Current chunk
            batch: Batch context

        Returns:
            List of validation error messages
        """
        errors = []
        if not chunk.metadata:
            return errors

        # Use cached metadata keys if available
        batch_id = id(batch)
        if batch_id not in self._metadata_cache:
            if batch.chunks:
                first_chunk = batch.chunks[0]
                if first_chunk.metadata:
                    self._metadata_cache[batch_id] = set(first_chunk.metadata.keys())
                else:
                    self._metadata_cache[batch_id] = set()

        expected_keys = self._metadata_cache.get(batch_id, set())
        current_keys = set(chunk.metadata.keys())

        if expected_keys and current_keys != expected_keys:
            errors.append(f"Inconsistent metadata structure: {current_keys} vs {expected_keys}")

        return errors

    def _validate_sequence_order(self, batch: ChunkBatch) -> List[str]:
        """Validate sequence ordering efficiently.

        Args:
            batch: Batch to validate

        Returns:
            List of validation error messages
        """
        errors = []
        sequence_chunks = [
            (i, c.sequence_number)
            for i, c in enumerate(batch.chunks)
            if hasattr(c, "sequence_number")
        ]

        if sequence_chunks:
            # Check if sequence is strictly increasing
            for i in range(1, len(sequence_chunks)):
                prev_idx, prev_seq = sequence_chunks[i - 1]
                curr_idx, curr_seq = sequence_chunks[i]
                if curr_seq <= prev_seq:
                    errors.append(
                        f"Non-sequential order at positions {prev_idx}-{curr_idx}: "
                        f"{prev_seq} -> {curr_seq}"
                    )

        return errors

    def validate(self, chunk: Chunk, metadata: Optional[Dict] = None) -> List[str]:
        """Validate chunk in batch context with optimized processing.

        Args:
            chunk: Current chunk to validate
            metadata: Must contain 'batch' key with ChunkBatch instance

        Returns:
            List of validation error messages
        """
        errors = []

        if not metadata or "batch" not in metadata:
            return errors  # Skip batch validation if no batch context

        batch = metadata["batch"]
        if not isinstance(batch, ChunkBatch):
            return errors

        # Validate batch size
        if len(batch.chunks) > self.max_batch_size:
            errors.append(
                f"Batch size {len(batch.chunks)} exceeds maximum of {self.max_batch_size}"
            )

        # Check memory usage
        estimated_memory = self._estimate_memory_usage(batch)
        if estimated_memory > self._max_memory_bytes:
            errors.append(
                f"Estimated memory usage {estimated_memory / 1024 / 1024:.1f}MB "
                f"exceeds limit of {self._max_memory_bytes / 1024 / 1024:.1f}MB"
            )

        # Validate metadata consistency
        errors.extend(self._validate_metadata_consistency(chunk, batch))

        # Validate sequence order
        errors.extend(self._validate_sequence_order(batch))

        return errors

    def cleanup(self) -> None:
        """Clean up cached data."""
        self._metadata_cache.clear()
