"""Search operations for the pipeline.

This module implements search functionality for the pipeline, providing both
semantic and hybrid search capabilities. It integrates with the vector index
and embedding generator to enable efficient document retrieval.

Features:
1. Search Types:
   - Semantic search using embeddings
   - Hybrid search combining text and vectors
   - Topic-based search and clustering
   - Similarity scoring

2. Performance Optimization:
   - Query embedding caching
   - Result filtering
   - Score thresholding
   - Batch processing

3. Result Management:
   - Score normalization
   - Result ranking
   - Metadata enrichment
   - Format standardization

Usage:
    ```python
    from pipeline.search import SearchOperations
    from src.embeddings.embedding_generator import EmbeddingGenerator
    from src.indexing.vector_index import VectorIndex
    from src.utils.topic_clustering import TopicClusterer

    # Initialize search operations
    search_ops = SearchOperations(
        embedding_generator=embedding_generator,
        vector_index=vector_index,
        topic_clusterer=topic_clusterer,
        logger=logger
    )

    # Perform search
    results = search_ops.search(
        query_text="example query",
        limit=10,
        min_score=0.7
    )
    ```

Note:
    - Supports multiple search modes
    - Handles query preprocessing
    - Includes error handling
    - Provides detailed logging
"""

import logging
from typing import Dict, List, Optional

from src.embeddings.embedding_generator import EmbeddingGenerator
from src.indexing.vector_index import VectorIndex
from src.utils.topic_clustering import TopicClusterer


class SearchOperations:
    """Handles all search-related operations in the pipeline.

    This class provides a unified interface for various search operations,
    including semantic search, hybrid search, and topic-based search.
    """

    def __init__(
        self,
        embedding_generator: EmbeddingGenerator,
        vector_index: VectorIndex,
        topic_clusterer: TopicClusterer,
        logger: logging.Logger,
    ):
        """Initialize search operations.

        Args:
            embedding_generator: For generating query embeddings
            vector_index: For performing vector similarity search
            topic_clusterer: For topic-based search and clustering
            logger: For operation logging
        """
        self.embedding_generator = embedding_generator
        self.vector_index = vector_index
        self.topic_clusterer = topic_clusterer
        self.logger = logger

    def search(
        self,
        query_text: str,
        query_vector: Optional[List[float]] = None,
        limit: int = 10,
        min_score: float = 0.7,
        use_hybrid: bool = True,
    ) -> List[Dict]:
        """Search for documents using text and/or vector similarity.

        Performs semantic or hybrid search based on the provided query and
        parameters. Supports both text-based and vector-based queries.

        Args:
            query_text: Text query for search
            query_vector: Optional pre-computed query embedding
            limit: Maximum number of results to return
            min_score: Minimum similarity score threshold
            use_hybrid: Whether to use hybrid search when possible

        Returns:
            List of search results with scores and metadata

        Example:
            >>> results = search_ops.search(
            ...     query_text="machine learning",
            ...     limit=5,
            ...     min_score=0.8
            ... )
        """
        try:
            self.logger.debug(
                "Starting search operation with query_text='%s', limit=%d, min_score=%.2f, use_hybrid=%s",
                query_text,
                limit,
                min_score,
                use_hybrid,
            )

            if query_vector is None and query_text:
                self.logger.debug("Generating embedding for text query")
                query_vector = self.embedding_generator._get_embedding(query_text)
                self.logger.debug("Successfully generated query embedding")

            if use_hybrid and query_text and query_vector:
                self.logger.debug("Performing hybrid search")
                results = self.vector_index.hybrid_search(
                    text_query=query_text, query_vector=query_vector, limit=limit
                )
                self.logger.debug("Hybrid search returned %d results", len(results))
            elif query_vector:
                self.logger.debug("Performing semantic search")
                results = self.vector_index.semantic_search(
                    query_vector=query_vector, limit=limit, min_score=min_score
                )
                self.logger.debug("Semantic search returned %d results", len(results))
            else:
                self.logger.error("No valid search criteria provided")
                return []

            self.logger.debug("Search operation completed successfully")
            return results

        except Exception as e:
            self.logger.error(f"Search error: {str(e)}")
            return []

    def find_similar_topics(
        self, query_text: str, documents: List[Dict], top_k: int = 5
    ) -> List[Dict]:
        """Find topics similar to a query.

        Identifies topics in the document collection that are semantically
        similar to the provided query text.

        Args:
            query_text: Text to find similar topics for
            documents: Collection of documents to search
            top_k: Number of similar topics to return

        Returns:
            List of similar topics with scores and metadata

        Example:
            >>> topics = search_ops.find_similar_topics(
            ...     query_text="artificial intelligence",
            ...     documents=docs,
            ...     top_k=3
            ... )
        """
        try:
            self.logger.debug(
                "Starting similar topics search with query='%s', top_k=%d", query_text, top_k
            )

            # Generate embedding for query
            self.logger.debug("Generating embedding for query text")
            query_vector = self.embedding_generator._get_embedding(query_text)
            self.logger.debug("Successfully generated query embedding")

            # Find similar topics
            self.logger.debug("Finding similar topics in %d documents", len(documents))
            results = self.topic_clusterer.find_similar_topics(
                query_vector=query_vector, documents=documents, top_k=top_k
            )
            self.logger.debug("Found %d similar topics", len(results))
            return results

        except Exception as e:
            self.logger.error(f"Topic search error: {str(e)}")
            return []
