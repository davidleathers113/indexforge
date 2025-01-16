"""Weaviate faceted search operations."""

import json
import time

from weaviate.classes.query import Filter

from src.api.errors.weaviate_error_handling import with_weaviate_error_handling
from src.api.models.requests import FacetQuery
from src.api.models.responses import FacetResponse, FacetResult, SearchResponse, SearchResult
from src.api.repositories.weaviate.base import BaseWeaviateRepository


class FacetedRepository(BaseWeaviateRepository):
    """Repository for faceted search operations."""

    @with_weaviate_error_handling
    async def faceted_search(
        self,
        query: FacetQuery,
        facets: list[str],
        cursor: str | None = None,
        sort_by: str | None = None,
        sort_order: str = "desc",
    ) -> tuple[SearchResponse, FacetResponse, str | None]:
        """Perform faceted search with aggregations.

        Args:
            query: Search parameters
            facets: List of fields to facet on
            cursor: Optional cursor for pagination
            sort_by: Optional field to sort by
            sort_order: Sort order ("asc" or "desc")

        Returns:
            Tuple of SearchResponse, FacetResponse and next cursor (if available)
        """
        start_time = time.time()

        # Build query
        query_builder = self.collection_ref.query.fetch_objects(
            properties=["title", "content", "file_path", "file_type", "metadata_json"],
            return_properties=self._get_include_properties(),
        )

        # Add filters
        filters = self._build_facet_filters(query.filters)
        if filters:
            query_builder = query_builder.with_where(filters)

        # Add sorting if specified
        if sort_by:
            query_builder = query_builder.with_sort({sort_by: sort_order})

        # Add pagination
        if cursor:
            query_builder = query_builder.with_after(cursor)
        else:
            query_builder = query_builder.with_limit(query.limit)

        # Execute query
        result = query_builder.do()

        # Format search results
        search_results = []
        for obj in result.objects:
            metadata = json.loads(obj.properties.get("metadata_json", "{}"))
            search_results.append(
                SearchResult(
                    id=obj.id,
                    title=obj.properties.get("title", ""),
                    content=obj.properties.get("content", ""),
                    file_path=obj.properties.get("file_path", ""),
                    file_type=obj.properties.get("file_type", ""),
                    metadata=metadata,
                    score=1.0,  # No relevance score for faceted results
                )
            )

        # Get facet aggregations
        facet_results = await self._get_facet_aggregations(facets, filters)

        # Get next cursor if there are more results
        next_cursor = result.after if len(search_results) == query.limit else None

        return (
            SearchResponse(
                results=search_results,
                total=len(search_results),
                took=(time.time() - start_time) * 1000,
            ),
            FacetResponse(facets=facet_results),
            next_cursor,
        )

    def _build_facet_filters(self, filters: dict[str, list[str]] | None) -> Filter | None:
        """Build filter from facet selections.

        Args:
            filters: Dictionary of field to selected values

        Returns:
            Combined filter or None if no filters
        """
        if not filters:
            return None

        filter_conditions = []
        for field, values in filters.items():
            if values:
                filter_conditions.append(Filter.by_property(field).contains_any(values))

        return self._build_filter(filter_conditions)

    async def _get_facet_aggregations(
        self, facets: list[str], filters: Filter | None = None
    ) -> list[FacetResult]:
        """Get aggregations for faceted fields.

        Args:
            facets: List of fields to facet on
            filters: Optional filter to apply

        Returns:
            List of facet results with counts
        """
        results = []
        for field in facets:
            # Build aggregation query
            agg_query = (
                self.collection_ref.aggregate.over_all()
                .with_group_by([field])
                .with_fields("groupedBy { value } count")
            )

            # Add filters if specified
            if filters:
                agg_query = agg_query.with_where(filters)

            # Execute aggregation
            result = agg_query.do()

            # Extract counts
            counts = {}
            for group in result.groups:
                value = group.grouped_by.get("value")
                if value:
                    counts[value] = group.count

            results.append(
                FacetResult(
                    field=field,
                    counts=counts,
                )
            )

        return results
