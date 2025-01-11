"""Weaviate repository for data access."""

import json
import logging
import time
from typing import Dict, List, Optional, Tuple

import weaviate.classes as wvc
from weaviate.classes.query import Filter
from weaviate.types import Include
from weaviate.util import generate_uuid5

from src.api.errors.weaviate_error_handling import with_weaviate_error_handling
from src.api.models.requests import DocumentFilter, SearchQuery
from src.api.models.responses import SearchResponse, SearchResult

logger = logging.getLogger(__name__)


class WeaviateRepository:
    """Repository for Weaviate operations."""

    def __init__(self, client: wvc.WeaviateClient, collection: str):
        """Initialize repository.

        Args:
            client: Weaviate client instance
            collection: Collection name to operate on
        """
        self.client = client
        self.collection = collection

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

        try:
            # Get collection reference
            collection = self.client.collections.get(self.collection)

            # Build query
            query_builder = collection.query.fetch_objects(
                properties=["title", "content", "file_path", "file_type", "metadata_json"],
                return_properties=Include.ALL,  # Include all metadata
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
                collection.aggregate.over_all()
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

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise

    @with_weaviate_error_handling
    async def filter_documents(
        self,
        filter_params: DocumentFilter,
        limit: int = 10,
        cursor: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> Tuple[SearchResponse, Optional[str]]:
        """Filter documents with advanced options.

        Args:
            filter_params: Filter criteria
            limit: Maximum number of results
            cursor: Optional cursor for pagination
            sort_by: Optional field to sort by
            sort_order: Sort order ("asc" or "desc")

        Returns:
            Tuple of SearchResponse and next cursor (if available)
        """
        start_time = time.time()

        try:
            # Get collection reference
            collection = self.client.collections.get(self.collection)

            # Build filters
            filters = []
            if filter_params.file_type:
                filters.append(Filter.by_property("file_type").equal(filter_params.file_type))

            if filter_params.date_from:
                filters.append(
                    Filter.by_property("metadata_json.modified_at").greater_than(
                        filter_params.date_from.isoformat()
                    )
                )

            if filter_params.date_to:
                filters.append(
                    Filter.by_property("metadata_json.modified_at").less_than(
                        filter_params.date_to.isoformat()
                    )
                )

            # Build query
            query_builder = collection.query.fetch_objects(
                properties=["title", "content", "file_path", "file_type", "metadata_json"],
                return_properties=Include.ALL,
            ).with_where(Filter.and_(filters) if filters else None)

            # Add sorting if specified
            if sort_by:
                query_builder = query_builder.with_sort({sort_by: sort_order})

            # Add pagination
            if cursor:
                query_builder = query_builder.with_after(cursor)
            else:
                query_builder = query_builder.with_limit(limit)

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
                        score=1.0,  # No relevance score for filtered results
                    )
                )

            # Get next cursor if there are more results
            next_cursor = result.after if len(search_results) == limit else None

            return (
                SearchResponse(
                    results=search_results,
                    total=len(search_results),
                    took=(time.time() - start_time) * 1000,
                ),
                next_cursor,
            )

        except Exception as e:
            logger.error(f"Filter failed: {str(e)}")
            raise

    # New document operations
    @with_weaviate_error_handling
    async def index_single_document(self, document: Dict) -> str:
        """Index a single document.

        Args:
            document: Document to index

        Returns:
            Document ID
        """
        # Generate deterministic UUID based on file path
        doc_id = generate_uuid5(document["file_path"])

        # Index document
        self.client.data_object.create(
            data_object=document,
            class_name=self.collection,
            uuid=doc_id,
        )

        return str(doc_id)

    @with_weaviate_error_handling
    async def list_documents(
        self, file_type: Optional[str] = None, limit: int = 10, offset: int = 0
    ) -> List[Dict]:
        """List indexed documents with optional filtering.

        Args:
            file_type: Optional file type filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of document metadata
        """
        # Build query
        query = self.client.query.get(
            self.collection, ["title", "file_path", "file_type", "metadata"]
        )

        # Add file type filter if specified
        if file_type:
            query = query.with_where(
                {"path": ["file_type"], "operator": "Equal", "valueString": file_type.lower()}
            )

        # Add pagination
        query = query.with_limit(limit).with_offset(offset)

        # Execute query
        result = query.do()

        # Extract documents
        documents = result.get("data", {}).get("Get", {}).get(self.collection, [])
        return documents

    @with_weaviate_error_handling
    async def get_document(self, document_id: str) -> Optional[Dict]:
        """Get a specific document by ID.

        Args:
            document_id: Document identifier

        Returns:
            Document metadata and content if found, None otherwise
        """
        # Query document by ID
        result = (
            self.client.query.get(
                self.collection, ["title", "content", "file_path", "file_type", "metadata"]
            )
            .with_where({"path": ["id"], "operator": "Equal", "valueString": document_id})
            .with_limit(1)
            .do()
        )

        # Extract document
        documents = result.get("data", {}).get("Get", {}).get(self.collection, [])
        return documents[0] if documents else None

    @with_weaviate_error_handling
    async def delete_document(self, document_id: str) -> bool:
        """Delete a specific document.

        Args:
            document_id: Document identifier

        Returns:
            True if document was deleted, False if not found
        """
        # Check if document exists
        if not await self.get_document(document_id):
            return False

        # Delete document
        self.client.data_object.delete(
            uuid=document_id,
            class_name=self.collection,
        )
        return True
