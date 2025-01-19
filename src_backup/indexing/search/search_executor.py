"""
Executes various types of search operations against a Weaviate vector database.

This module provides the SearchExecutor class which implements different search strategies
including semantic search, hybrid search, time-range search, and relationship-based search.
It handles the execution of queries and processes the results into a standardized format.

The module integrates with Weaviate's Python client and includes comprehensive error
handling and logging for production use.

Example:
    ```python
    client = weaviate.Client("http://localhost:8080")
    executor = SearchExecutor(client, "Document")
    results = executor.semantic_search(
        query_vector=[0.1, 0.2, 0.3],
        limit=5,
        min_score=0.8
    )
    for result in results:
        print(f"Found document: {result.title} (score: {result.score})")
    ```
"""

from datetime import datetime
import logging

import weaviate

from .search_result import ResultProcessor, SearchResult


class SearchExecutor:
    """
    Executes search operations against a Weaviate vector database.

    This class provides methods to perform various types of searches including:
    - Semantic search using vector similarity
    - Hybrid search combining vector and text-based search
    - Time range filtering with optional vector similarity
    - Relationship-based search for finding related documents

    The executor handles query execution, error handling, logging, and result
    processing. It works in conjunction with the ResultProcessor to convert
    raw Weaviate responses into structured SearchResult objects.

    Attributes:
        client: The Weaviate client instance used for executing queries
        class_name: The name of the document class in Weaviate
        logger: Logger instance for debugging and error tracking
        result_processor: Instance of ResultProcessor for handling query results
    """

    def __init__(self, client: weaviate.Client, class_name: str):
        """
        Initialize a new SearchExecutor instance.

        Args:
            client: A configured Weaviate client instance for database operations
            class_name: The name of the class/collection in Weaviate to query against

        Raises:
            TypeError: If client is not a weaviate.Client instance
            ValueError: If class_name is empty or not a string
        """
        self.client = client
        self.class_name = class_name
        self.logger = logging.getLogger(__name__)
        self.result_processor = ResultProcessor()

    def semantic_search(
        self,
        query_vector: list[float],
        limit: int = 10,
        min_score: float = 0.7,
        additional_props: list[str] | None = None,
        with_vector: bool = False,
    ) -> list[SearchResult]:
        """
        Execute a semantic search using vector similarity.

        Performs a search operation based on vector similarity to find documents
        that are semantically similar to the provided query vector. The search
        uses cosine similarity as the distance metric.

        Args:
            query_vector: Vector embedding representing the search query
            limit: Maximum number of results to return (default: 10)
            min_score: Minimum similarity score threshold (0-1) (default: 0.7)
            additional_props: Additional properties to include in results
            with_vector: Whether to include vectors in results (default: False)

        Returns:
            List[SearchResult]: A list of search results ordered by similarity score

        Raises:
            ValueError: If query_vector is empty or contains non-float values
            ValueError: If min_score is not between 0 and 1
            ValueError: If limit is less than 1

        Example:
            ```python
            results = executor.semantic_search(
                query_vector=[0.1, 0.2, 0.3],
                limit=5,
                min_score=0.8,
                additional_props=["category"]
            )
            for result in results:
                print(f"Score: {result.score}, Title: {result.content_title}")
            ```
        """
        try:
            self.logger.info(
                f"Executing semantic search with parameters: limit={limit}, min_score={min_score}"
            )
            self.logger.debug(f"Query vector length: {len(query_vector)}")
            if additional_props:
                self.logger.debug(f"Additional properties requested: {additional_props}")
            if with_vector:
                self.logger.debug("Vector return requested")

            properties = [
                "content_body",
                "content_summary",
                "content_title",
                "timestamp_utc",
                "schema_version",
                "parent_id",
                "chunk_ids",
            ]
            if additional_props:
                properties.extend(additional_props)
                self.logger.debug(f"Total properties to fetch: {properties}")

            additional = ["id", "score"]
            if with_vector:
                additional.append("vector")
            self.logger.debug(f"Additional fields to fetch: {additional}")

            query = (
                self.client.query.get(self.class_name, properties)
                .with_additional(additional)
                .with_near_vector({"vector": query_vector, "certainty": min_score})
                .with_limit(limit)
            )
            self.logger.debug("Query built successfully")

            result = query.do()
            if not result:
                self.logger.warning("No results returned from query")
                return []
            if "data" not in result:
                self.logger.warning("Invalid result format - missing 'data' key")
                return []

            # Process results into SearchResult objects
            search_results = self.result_processor.process_results(result)
            self.logger.info(f"Found {len(search_results)} matching documents")

            # Log quality metrics
            if search_results:
                scores = [result.score for result in search_results]
                avg_score = sum(scores) / len(scores) if scores else 0
                max_score = max(scores) if scores else 0
                self.logger.info(
                    f"Search quality metrics - Average score: {avg_score:.3f}, "
                    f"Max score: {max_score:.3f}"
                )

            return search_results
        except Exception as e:
            self.logger.error(
                f"Error in semantic search: {e!s}",
                exc_info=True,
                extra={
                    "vector_length": len(query_vector),
                    "limit": limit,
                    "min_score": min_score,
                    "with_vector": with_vector,
                },
            )
            return []

    def hybrid_search(
        self,
        text_query: str,
        query_vector: list[float],
        limit: int = 10,
        alpha: float = 0.5,
        additional_props: list[str] | None = None,
        with_vector: bool = False,
    ) -> list[dict]:
        """
        Execute a hybrid search combining text and vector similarity.

        Performs a search that combines traditional text-based search (BM25) with
        vector similarity search. The alpha parameter controls the balance between
        the two search methods.

        Args:
            text_query: Text string to search for using BM25
            query_vector: Vector embedding for similarity search
            limit: Maximum number of results to return (default: 10)
            alpha: Weight between text (0) and vector (1) search (default: 0.5)
            additional_props: Additional properties to include in results
            with_vector: Whether to include vectors in results (default: False)

        Returns:
            List[Dict]: A list of search results ordered by combined score

        Raises:
            ValueError: If text_query is empty
            ValueError: If query_vector is invalid
            ValueError: If alpha is not between 0 and 1
            Exception: If the search operation fails

        Example:
            ```python
            results = executor.hybrid_search(
                text_query="machine learning",
                query_vector=[0.1, 0.2, 0.3],
                alpha=0.7
            )
            ```
        """
        try:
            properties = [
                "content_body",
                "content_summary",
                "content_title",
                "timestamp_utc",
                "schema_version",
                "parent_id",
                "chunk_ids",
            ]
            if additional_props:
                properties.extend(additional_props)

            additional = ["id", "score"]
            if with_vector:
                additional.append("vector")

            query = (
                self.client.query.get(self.class_name, properties)
                .with_additional(additional)
                .with_near_vector({"vector": query_vector, "certainty": alpha})
                .with_bm25({"query": text_query})
                .with_limit(limit)
            )
            result = query.do_get()
            if not result or "data" not in result:
                return []
            return result["data"]["Get"][self.class_name]
        except Exception as e:
            self.logger.error(f"Error in hybrid search: {e!s}")
            return []

    def time_range_search(
        self,
        start_time: datetime,
        end_time: datetime,
        query_vector: list[float] | None = None,
        limit: int = 10,
        additional_props: list[str] | None = None,
    ) -> list[dict]:
        """
        Execute a search within a specific time range.

        Searches for documents with timestamps falling within the specified time range.
        Optionally combines the time filter with vector similarity search if a
        query vector is provided.

        Args:
            start_time: Start of the time range (inclusive)
            end_time: End of the time range (inclusive)
            query_vector: Optional vector for similarity search
            limit: Maximum number of results to return (default: 10)
            additional_props: Additional properties to include in results

        Returns:
            List[Dict]: A list of documents within the time range

        Raises:
            ValueError: If end_time is before start_time
            ValueError: If query_vector is provided but invalid
            Exception: If the search operation fails

        Example:
            ```python
            from datetime import datetime, timedelta

            end = datetime.now()
            start = end - timedelta(days=7)
            results = executor.time_range_search(
                start_time=start,
                end_time=end,
                limit=20
            )
            ```
        """
        try:
            properties = [
                "content_body",
                "content_summary",
                "content_title",
                "timestamp_utc",
                "schema_version",
                "parent_id",
                "chunk_ids",
            ]
            if additional_props:
                properties.extend(additional_props)

            where_filter = {
                "path": ["timestamp_utc"],
                "operator": "And",
                "operands": [
                    {
                        "operator": "GreaterThanEqual",
                        "valueDate": start_time.isoformat(),
                    },
                    {
                        "operator": "LessThanEqual",
                        "valueDate": end_time.isoformat(),
                    },
                ],
            }

            query = (
                self.client.query.get(self.class_name, properties)
                .with_additional(["id"])
                .with_where(where_filter)
            )

            if query_vector:
                query = query.with_near_vector({"vector": query_vector})

            query = query.with_limit(limit)
            result = query.do_get()
            if not result or "data" not in result:
                return []
            return result["data"]["Get"][self.class_name]
        except Exception as e:
            self.logger.error(f"Error in time range search: {e!s}")
            return []

    def relationship_search(
        self,
        parent_id: str,
        query_vector: list[float] | None = None,
        limit: int = 10,
        additional_props: list[str] | None = None,
    ) -> list[dict]:
        """
        Execute a search for documents related to a specific parent.

        Searches for documents that have a relationship with a specified parent
        document. Optionally combines the relationship filter with vector
        similarity search if a query vector is provided.

        Args:
            parent_id: ID of the parent document to find related documents for
            query_vector: Optional vector for similarity search
            limit: Maximum number of results to return (default: 10)
            additional_props: Additional properties to include in results

        Returns:
            List[Dict]: A list of related documents

        Raises:
            ValueError: If parent_id is empty
            ValueError: If query_vector is provided but invalid
            Exception: If the search operation fails

        Example:
            ```python
            results = executor.relationship_search(
                parent_id="12345",
                query_vector=[0.1, 0.2, 0.3],
                limit=5
            )
            ```
        """
        try:
            properties = [
                "content_body",
                "content_summary",
                "content_title",
                "timestamp_utc",
                "schema_version",
                "parent_id",
                "chunk_ids",
            ]
            if additional_props:
                properties.extend(additional_props)

            where_filter = {
                "path": ["parent_id"],
                "operator": "Equal",
                "valueString": parent_id,
            }

            query = (
                self.client.query.get(self.class_name, properties)
                .with_additional(["id"])
                .with_where(where_filter)
            )

            if query_vector:
                query = query.with_near_vector({"vector": query_vector})

            query = query.with_limit(limit)
            result = query.do_get()
            if not result or "data" not in result:
                return []
            return result["data"]["Get"][self.class_name]
        except Exception as e:
            self.logger.error(f"Error in relationship search: {e!s}")
            return []
