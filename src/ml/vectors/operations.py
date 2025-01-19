"""Vector indexing utilities.

This module provides utilities for efficient vector indexing and similarity search
using FAISS.
"""

import logging
from typing import Optional, Tuple

import faiss
import numpy as np

from .exceptions import DimensionMismatchError, ResourceError, VectorIndexError

logger = logging.getLogger(__name__)


class VectorIndex:
    """FAISS-based vector indexing and similarity search."""

    def __init__(
        self,
        dimension: int,
        index_type: str = "L2",
        gpu_id: Optional[int] = None,
    ) -> None:
        """Initialize the vector index.

        Args:
            dimension: Dimensionality of the vectors
            index_type: Type of index to use ('L2' or 'IP' for inner product)
            gpu_id: Optional GPU device ID to use

        Raises:
            VectorIndexError: If parameters are invalid
            ResourceError: If GPU initialization fails
        """
        if dimension <= 0:
            raise VectorIndexError("Dimension must be positive")

        try:
            if index_type == "L2":
                self.index = faiss.IndexFlatL2(dimension)
            elif index_type == "IP":
                self.index = faiss.IndexFlatIP(dimension)
            else:
                raise VectorIndexError(f"Unsupported index type: {index_type}")

            self._gpu_resources = None
            if gpu_id is not None:
                try:
                    self._gpu_resources = faiss.StandardGpuResources()
                    self.index = faiss.index_cpu_to_gpu(self._gpu_resources, gpu_id, self.index)
                    logger.info("Using GPU device %d for vector index", gpu_id)
                except Exception as e:
                    logger.warning("Failed to use GPU, falling back to CPU: %s", str(e))
                    if self._gpu_resources is not None:
                        self._gpu_resources.delete()
                        self._gpu_resources = None
                    raise ResourceError(f"Failed to initialize GPU resources: {str(e)}") from e

            self.dimension = dimension
            logger.info(
                "Initialized VectorIndex with dimension=%d, type=%s",
                dimension,
                index_type,
            )
        except Exception as e:
            logger.exception("Failed to initialize vector index: %s", str(e))
            raise VectorIndexError(f"Failed to initialize vector index: {str(e)}") from e

    def add_vectors(self, vectors: np.ndarray, ids: Optional[np.ndarray] = None) -> None:
        """Add vectors to the index.

        Args:
            vectors: Matrix of vectors to add (n_vectors x dimension)
            ids: Optional array of vector IDs

        Raises:
            DimensionMismatchError: If vectors have wrong shape
            VectorIndexError: If adding vectors fails
        """
        if vectors.ndim != 2 or vectors.shape[1] != self.dimension:
            raise DimensionMismatchError(
                f"Vectors must have shape (n_vectors, {self.dimension}), " f"got {vectors.shape}"
            )

        if ids is not None and len(ids) != len(vectors):
            raise VectorIndexError("Number of IDs must match number of vectors")

        try:
            if ids is not None:
                self.index.add_with_ids(vectors, ids)
            else:
                self.index.add(vectors)
            logger.debug("Added %d vectors to index", len(vectors))
        except Exception as e:
            logger.exception("Failed to add vectors: %s", str(e))
            raise VectorIndexError(f"Failed to add vectors: {str(e)}") from e

    def search(
        self,
        query_vectors: np.ndarray,
        k: int = 5,
        return_distances: bool = True,
    ) -> Tuple[np.ndarray, np.ndarray] | np.ndarray:
        """Search for nearest neighbors.

        Args:
            query_vectors: Query vectors (n_queries x dimension)
            k: Number of nearest neighbors to return
            return_distances: Whether to return distances with indices

        Returns:
            If return_distances is True:
                Tuple of (distances, indices) arrays
            Otherwise:
                Array of indices only

        Raises:
            DimensionMismatchError: If query vectors have wrong shape
            VectorIndexError: If search fails
        """
        if query_vectors.ndim != 2 or query_vectors.shape[1] != self.dimension:
            raise DimensionMismatchError(
                f"Query vectors must have shape (n_queries, {self.dimension}), "
                f"got {query_vectors.shape}"
            )

        if k <= 0:
            raise VectorIndexError("k must be positive")

        if k > self.index.ntotal:
            logger.warning(
                "Requested k=%d but index only contains %d vectors",
                k,
                self.index.ntotal,
            )
            k = max(1, self.index.ntotal)

        try:
            distances, indices = self.index.search(query_vectors, k)
            logger.debug(
                "Searched %d queries for %d nearest neighbors",
                len(query_vectors),
                k,
            )
            return (distances, indices) if return_distances else indices
        except Exception as e:
            logger.exception("Failed to search vectors: %s", str(e))
            raise VectorIndexError(f"Failed to search vectors: {str(e)}") from e

    def get_size(self) -> int:
        """Get the number of vectors in the index.

        Returns:
            Number of indexed vectors
        """
        return self.index.ntotal

    def reset(self) -> None:
        """Reset the index, removing all vectors."""
        self.index.reset()
        logger.info("Reset vector index")

    def __del__(self):
        """Clean up GPU resources."""
        if self._gpu_resources is not None:
            try:
                self._gpu_resources.delete()
                logger.debug("Cleaned up GPU resources")
            except Exception as e:
                logger.exception("Failed to clean up GPU resources: %s", str(e))
