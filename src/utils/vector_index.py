"""Vector index for efficient similarity search.

This module provides functionality for creating and managing vector indices
for efficient similarity search over document embeddings.

Classes:
    VectorIndex: Main class for managing vector indices.

Example:
    ```python
    index = VectorIndex(dimension=768)
    index.add_vectors(embeddings, ids)
    results = index.search(query_embedding, k=5)
    ```
"""


from faiss import IndexFlatL2
import numpy as np


class VectorIndex:
    """Manages vector indices for efficient similarity search."""

    def __init__(self, dimension: int = 768):
        """Initialize the vector index.

        Args:
            dimension: Dimensionality of the vectors to index.
                Defaults to 768 (BERT base model dimension).
        """
        self.dimension = dimension
        self.index = IndexFlatL2(dimension)
        self.id_map = {}

    def add_vectors(
        self,
        vectors: list[list[float]] | np.ndarray,
        ids: list[str] | None = None,
    ) -> None:
        """Add vectors to the index.

        Args:
            vectors: List of vectors or numpy array of shape (n, dimension).
            ids: Optional list of string IDs for the vectors.
                If None, sequential integers will be used.
        """
        if isinstance(vectors, list):
            vectors = np.array(vectors, dtype=np.float32)
        if ids is not None:
            for i, id_ in enumerate(ids):
                self.id_map[i] = id_
        self.index.add(vectors)

    def search(
        self, query: list[float] | np.ndarray, k: int = 5
    ) -> tuple[np.ndarray, np.ndarray]:
        """Search for nearest neighbors.

        Args:
            query: Query vector or numpy array of shape (dimension,).
            k: Number of nearest neighbors to return.

        Returns:
            Tuple of (distances, indices) arrays.
        """
        if isinstance(query, list):
            query = np.array(query, dtype=np.float32).reshape(1, -1)
        distances, indices = self.index.search(query, k)
        if self.id_map:
            indices = np.array([[self.id_map.get(i, i) for i in row] for row in indices])
        return distances, indices
