"""Weaviate query builder."""

from typing import Any, Dict, List, Optional

from weaviate.classes import Collection
from weaviate.classes.query import Filter
from weaviate.types import Include

from src.api.models.requests import SearchQuery


class QueryBuilder:
    """Builder for Weaviate queries."""

    def __init__(self, collection: Collection):
        """Initialize query builder.

        Args:
            collection: Collection reference to build queries for
        """
        self.collection = collection
        self.query = collection.query.fetch_objects(
            properties=["title", "content", "file_path", "file_type", "metadata_json"]
        )
        self._filters: List[Filter] = []
        self._include_vector = False
        self._limit: Optional[int] = None
        self._cursor: Optional[str] = None
        self._sort: Optional[Dict[str, str]] = None

    def with_vector_search(self, vector: List[float], certainty: float = 0.7) -> "QueryBuilder":
        """Add vector search to query.

        Args:
            vector: Vector to search for
            certainty: Minimum certainty threshold

        Returns:
            Self for chaining
        """
        self.query = self.query.with_near_vector({"vector": vector, "certainty": certainty})
        return self

    def with_hybrid_search(
        self,
        query: str,
        alpha: float = 0.5,
        properties: Optional[List[str]] = None,
        fusion_type: str = "relative_score",
    ) -> "QueryBuilder":
        """Add hybrid search to query.

        Args:
            query: Text to search for
            alpha: Balance between vector and keyword search
            properties: Properties to search in
            fusion_type: Type of fusion to use

        Returns:
            Self for chaining
        """
        self.query = self.query.with_hybrid(
            query=query,
            alpha=alpha,
            properties=properties or ["title^2", "content"],
            fusion_type=fusion_type,
        )
        return self

    def with_bm25(self, b: float = 0.75, k1: float = 1.2) -> "QueryBuilder":
        """Add BM25 configuration to query.

        Args:
            b: Document length normalization
            k1: Term frequency saturation

        Returns:
            Self for chaining
        """
        self.query = self.query.with_bm25(b=b, k1=k1)
        return self

    def with_filter(self, filter_obj: Filter) -> "QueryBuilder":
        """Add filter to query.

        Args:
            filter_obj: Filter to add

        Returns:
            Self for chaining
        """
        self._filters.append(filter_obj)
        return self

    def with_pagination(
        self, limit: Optional[int] = None, cursor: Optional[str] = None
    ) -> "QueryBuilder":
        """Add pagination to query.

        Args:
            limit: Maximum number of results
            cursor: Cursor for pagination

        Returns:
            Self for chaining
        """
        self._limit = limit
        self._cursor = cursor
        return self

    def with_sort(self, field: str, order: str = "desc") -> "QueryBuilder":
        """Add sorting to query.

        Args:
            field: Field to sort by
            order: Sort order ("asc" or "desc")

        Returns:
            Self for chaining
        """
        self._sort = {field: order}
        return self

    def with_include_vector(self, include: bool = True) -> "QueryBuilder":
        """Include vector in results.

        Args:
            include: Whether to include vector

        Returns:
            Self for chaining
        """
        self._include_vector = include
        return self

    def build(self) -> Any:
        """Build and return final query.

        Returns:
            Built query ready for execution
        """
        # Apply filters if any
        if self._filters:
            self.query = self.query.with_where(Filter.and_(self._filters))

        # Apply sorting
        if self._sort:
            self.query = self.query.with_sort(self._sort)

        # Apply pagination
        if self._cursor:
            self.query = self.query.with_after(self._cursor)
        elif self._limit:
            self.query = self.query.with_limit(self._limit)

        # Set return properties
        include = Include.ALL
        if self._include_vector:
            include = Include.ALL | Include.VECTOR

        self.query = self.query.with_additional(include)

        return self.query

    @classmethod
    def from_search_query(cls, collection: Collection, search_query: SearchQuery) -> "QueryBuilder":
        """Create builder from search query.

        Args:
            collection: Collection reference
            search_query: Search parameters

        Returns:
            Configured query builder
        """
        builder = cls(collection)

        if search_query.query:
            builder.with_hybrid_search(search_query.query)

        if search_query.limit:
            builder.with_pagination(limit=search_query.limit)

        return builder
