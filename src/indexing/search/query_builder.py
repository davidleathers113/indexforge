"""
Provides query building operations for vector search in Weaviate database.

This module contains the QueryBuilder class which handles the construction of various
types of search queries including semantic, hybrid, time-range, and relationship-based
searches. It provides a clean interface for building complex Weaviate queries with
proper type hints and parameter validation.

Example:
    ```python
    client = weaviate.Client("http://localhost:8080")
    builder = QueryBuilder(client, "Document")
    query = builder.build_semantic_query(
        query_vector=[0.1, 0.2, 0.3],
        limit=5,
        min_score=0.8
    )
    ```
"""

from datetime import datetime
import logging

import weaviate


class QueryBuilder:
    """
    A builder class for constructing various types of Weaviate search queries.

    This class provides methods to build different types of search queries including:
    - Semantic search (vector similarity)
    - Hybrid search (combining vector and text)
    - Time range search
    - Relationship-based search

    The builder pattern allows for flexible query construction with optional parameters
    and proper type validation.

    Attributes:
        client: The Weaviate client instance used for queries
        class_name: The name of the document class in Weaviate
        logger: Logger instance for debugging and error tracking
    """

    def __init__(self, client: weaviate.Client, class_name: str):
        """
        Initialize a new QueryBuilder instance.

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

    def build_semantic_query(
        self,
        query_vector: list[float],
        limit: int = 10,
        min_score: float = 0.7,
        additional_props: list[str] | None = None,
    ) -> dict:
        """
        Build a semantic search query based on vector similarity.

        This method constructs a query that finds documents similar to the provided
        vector embedding, using cosine similarity as the distance metric.

        Args:
            query_vector: A list of floats representing the query embedding vector
            limit: Maximum number of results to return (default: 10)
            min_score: Minimum similarity score threshold (0-1) (default: 0.7)
            additional_props: List of additional properties to include in results

        Returns:
            Dict: A Weaviate query object ready for execution

        Raises:
            ValueError: If query_vector is empty or contains non-float values
            ValueError: If min_score is not between 0 and 1
            ValueError: If limit is less than 1

        Example:
            ```python
            query = builder.build_semantic_query(
                query_vector=[0.1, 0.2, 0.3],
                limit=5,
                min_score=0.8,
                additional_props=["category", "author"]
            )
            ```
        """
        query = (
            self.client.query.get(self.class_name)
            .with_near_vector({"vector": query_vector, "certainty": min_score})
            .with_limit(limit)
        )

        if additional_props:
            query = query.with_additional(additional_props)

        return query

    def build_hybrid_query(
        self,
        text_query: str,
        query_vector: list[float],
        limit: int = 10,
        alpha: float = 0.5,
        additional_props: list[str] | None = None,
    ) -> dict:
        """
        Build a hybrid search query combining text and vector similarity.

        This method creates a query that combines traditional text search with
        vector similarity search. The alpha parameter controls the balance between
        text and vector similarity in the final results.

        Args:
            text_query: The text string to search for
            query_vector: Vector embedding for similarity search
            limit: Maximum number of results to return (default: 10)
            alpha: Weight between text (0) and vector (1) search (default: 0.5)
            additional_props: List of additional properties to include in results

        Returns:
            Dict: A Weaviate query object ready for execution

        Raises:
            ValueError: If text_query is empty
            ValueError: If query_vector is empty or contains non-float values
            ValueError: If alpha is not between 0 and 1
            ValueError: If limit is less than 1

        Example:
            ```python
            query = builder.build_hybrid_query(
                text_query="machine learning",
                query_vector=[0.1, 0.2, 0.3],
                alpha=0.7
            )
            ```
        """
        query = (
            self.client.query.get(self.class_name)
            .with_hybrid(query=text_query, vector=query_vector, alpha=alpha)
            .with_limit(limit)
        )

        if additional_props:
            query = query.with_additional(additional_props)

        return query

    def build_time_range_query(
        self,
        start_time: datetime,
        end_time: datetime,
        query_vector: list[float] | None = None,
        limit: int = 10,
    ) -> dict:
        """
        Build a query to search for documents within a specific time range.

        This method creates a query that filters documents based on their timestamp,
        optionally combining it with vector similarity search if a query vector
        is provided.

        Args:
            start_time: Start of the time range (inclusive)
            end_time: End of the time range (inclusive)
            query_vector: Optional vector for similarity search
            limit: Maximum number of results to return (default: 10)

        Returns:
            Dict: A Weaviate query object ready for execution

        Raises:
            ValueError: If end_time is before start_time
            ValueError: If query_vector is provided but invalid
            ValueError: If limit is less than 1

        Example:
            ```python
            from datetime import datetime, timedelta

            end = datetime.now()
            start = end - timedelta(days=7)
            query = builder.build_time_range_query(
                start_time=start,
                end_time=end,
                limit=20
            )
            ```
        """
        where_filter = {
            "path": ["metadata", "timestamp_utc"],
            "operator": "And",
            "operands": [
                {"operator": "GreaterThanEqual", "valueDate": start_time.isoformat()},
                {"operator": "LessThanEqual", "valueDate": end_time.isoformat()},
            ],
        }

        query = self.client.query.get(self.class_name).with_where(where_filter).with_limit(limit)

        if query_vector:
            query = query.with_near_vector({"vector": query_vector})

        return query

    def build_relationship_query(
        self, parent_id: str, query_vector: list[float] | None = None, limit: int = 10
    ) -> dict:
        """
        Build a query to search for documents related to a specific parent document.

        This method creates a query that finds documents with a specific parent_id,
        optionally combining it with vector similarity search if a query vector
        is provided.

        Args:
            parent_id: The ID of the parent document to find related documents for
            query_vector: Optional vector for similarity search
            limit: Maximum number of results to return (default: 10)

        Returns:
            Dict: A Weaviate query object ready for execution

        Raises:
            ValueError: If parent_id is empty
            ValueError: If query_vector is provided but invalid
            ValueError: If limit is less than 1

        Example:
            ```python
            query = builder.build_relationship_query(
                parent_id="12345",
                query_vector=[0.1, 0.2, 0.3],
                limit=5
            )
            ```
        """
        where_filter = {"path": ["parent_id"], "operator": "Equal", "valueString": parent_id}

        query = self.client.query.get(self.class_name).with_where(where_filter).with_limit(limit)

        if query_vector:
            query = query.with_near_vector({"vector": query_vector})

        return query
