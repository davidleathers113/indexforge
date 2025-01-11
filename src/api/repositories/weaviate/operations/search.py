"""Weaviate search operations."""

import json
import time
from typing import Dict, List, Optional, Tuple

from src.api.errors.weaviate_error_handling import with_weaviate_error_handling
from src.api.models.requests import SearchQuery
from src.api.models.responses import SearchResponse, SearchResult
from src.api.repositories.weaviate.base import BaseWeaviateRepository


class SearchRepository(BaseWeaviateRepository):
    """Repository for search operations."""

    @with_weaviate_error_handling
    async def search(
        self,
        query: SearchQuery,
        cursor: Optional[str] = None,
        vector: Optional[List[float]] = None,
        bm25_config: Optional[Dict[str, float]] = None,
    ) -> Tuple[SearchResponse, Optional[str]]:
        """Perform semantic search with advanced features.

        Args:
            query: Search parameters
            cursor: Optional cursor for pagination
            vector: Optional vector for pure vector search
            bm25_config: Optional BM25 configuration (b and k1 parameters)

        Returns:
            Tuple of SearchResponse and next cursor (if available)
        """
        start_time = time.time()

        # Build query
        query_builder = self.collection_ref.query.fetch_objects(
            properties=["title", "content", "file_path", "file_type", "metadata_json"],
            return_properties=self._get_include_properties(include_vector=True),
        )

        # Configure search type based on inputs
        if vector is not None:
            # Pure vector search
            query_builder = query_builder.with_near_vector(
                {
                    "vector": vector,
                    "certainty": 0.7,  # Configurable threshold
                }
            )
        elif query.query:
            # Hybrid search with configurable parameters
            query_builder = query_builder.with_hybrid(
                query=query.query,
                alpha=0.5,  # Balance between vector and keyword search
                properties=["title^2", "content"],  # Boost title matches
                fusion_type="relative_score",  # Use relative scoring
            )

            # Add BM25 configuration if provided
            if bm25_config:
                query_builder = query_builder.with_bm25(
                    b=bm25_config.get("b", 0.75),
                    k1=bm25_config.get("k1", 1.2),
                )

        # Add pagination
        if cursor:
            query_builder = query_builder.with_after(cursor)
        else:
            query_builder = query_builder.with_limit(query.limit)

        # Execute query
        result = query_builder.do()

        # Format results
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
                    score=obj.score,
                    vector=obj.vector if hasattr(obj, "vector") else None,
                    certainty=obj.certainty if hasattr(obj, "certainty") else None,
                    distance=obj.distance if hasattr(obj, "distance") else None,
                )
            )

        # Get total count efficiently using aggregation
        total = (
            self.collection_ref.aggregate.over_all()
            .with_meta_count()
            .with_where(query_builder._where if hasattr(query_builder, "_where") else None)
            .do()
        )

        # Get next cursor if there are more results
        next_cursor = result.after if len(search_results) == query.limit else None

        return (
            SearchResponse(
                results=search_results,
                total=total.total_count,
                took=(time.time() - start_time) * 1000,
            ),
            next_cursor,
        )
