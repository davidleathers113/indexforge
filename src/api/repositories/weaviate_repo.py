"""Weaviate repository for data access."""

import json
import logging
import time
from typing import Dict, List, Optional

import weaviate
from weaviate.util import generate_uuid5

from src.api.models.requests import DocumentFilter, SearchQuery
from src.api.models.responses import SearchResponse, SearchResult, Stats

logger = logging.getLogger(__name__)


class WeaviateRepository:
    """Repository for Weaviate operations."""

    def __init__(self, client: weaviate.Client):
        """Initialize repository with Weaviate client.

        Args:
            client: Configured Weaviate client
        """
        self.client = client
        self.collection = "Document"

    async def search(self, query: SearchQuery) -> SearchResponse:
        """Perform semantic search.

        Args:
            query: Search parameters

        Returns:
            SearchResponse containing results and metadata
        """
        start_time = time.time()

        try:
            result = (
                self.client.query.get(
                    self.collection, ["title", "content", "file_path", "file_type", "metadata_json"]
                )
                .with_near_text({"concepts": [query.query]})
                .with_limit(query.limit)
                .with_offset(query.offset)
                .with_additional(["id", "score"])
                .do()
            )

            documents = result.get("data", {}).get("Get", {}).get("Document", [])

            # Format results
            search_results = []
            for doc in documents:
                metadata = json.loads(doc.get("metadata_json", "{}"))
                search_results.append(
                    SearchResult(
                        id=doc.get("_additional", {}).get("id", ""),
                        title=doc.get("title", ""),
                        content=doc.get("content", ""),
                        file_path=doc.get("file_path", ""),
                        file_type=doc.get("file_type", ""),
                        metadata=metadata,
                        score=doc.get("_additional", {}).get("score", 0.0),
                    )
                )

            # Get total count
            total = (
                self.client.query.aggregate(self.collection)
                .with_meta_count()
                .with_near_text({"concepts": [query.query]})
                .do()
            )
            total_count = (
                total.get("data", {})
                .get("Aggregate", {})
                .get("Document", [{}])[0]
                .get("meta", {})
                .get("count", 0)
            )

            return SearchResponse(
                results=search_results,
                total=total_count,
                took=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise

    async def get_stats(self) -> Stats:
        """Get collection statistics.

        Returns:
            Stats containing document counts and status
        """
        try:
            # Get total count
            result = self.client.query.aggregate(self.collection).with_meta_count().do()
            total_count = (
                result.get("data", {})
                .get("Aggregate", {})
                .get("Document", [{}])[0]
                .get("meta", {})
                .get("count", 0)
            )

            # Get counts by file type
            type_counts = (
                self.client.query.aggregate(self.collection)
                .with_group_by_filter("file_type")
                .with_fields("groupedBy { value count }")
                .do()
            )

            file_types = {}
            for group in type_counts.get("data", {}).get("Aggregate", {}).get("Document", []):
                file_type = group.get("groupedBy", {}).get("value")
                count = group.get("count", 0)
                if file_type:
                    file_types[file_type] = count

            return Stats(
                document_count=total_count,
                file_types=file_types,
                status="active" if total_count > 0 else "empty",
            )

        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}")
            raise

    async def filter_documents(
        self, filter_params: DocumentFilter, limit: int = 10, offset: int = 0
    ) -> SearchResponse:
        """Filter documents by parameters.

        Args:
            filter_params: Filter criteria
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            SearchResponse containing filtered results
        """
        start_time = time.time()

        try:
            # Build where filter
            where_filter = {}
            if filter_params.file_type:
                where_filter = {
                    "operator": "Equal",
                    "path": ["file_type"],
                    "valueString": filter_params.file_type,
                }

            # Execute query
            base_query = self.client.query.get(
                self.collection, ["title", "content", "file_path", "file_type", "metadata_json"]
            )

            # Add filter if specified
            query = base_query.with_where(where_filter) if where_filter else base_query

            # Add pagination and execute
            result = query.with_limit(limit).with_offset(offset).with_additional(["id"]).do()

            documents = result.get("data", {}).get("Get", {}).get("Document", [])

            # Format results
            search_results = []
            for doc in documents:
                metadata = json.loads(doc.get("metadata_json", "{}"))

                # Apply date filters if specified
                if filter_params.date_from or filter_params.date_to:
                    doc_date = metadata.get("modified_at") or metadata.get("created_at")
                    if not doc_date:
                        continue

                    if filter_params.date_from and doc_date < filter_params.date_from:
                        continue
                    if filter_params.date_to and doc_date > filter_params.date_to:
                        continue

                search_results.append(
                    SearchResult(
                        id=doc.get("_additional", {}).get("id", ""),
                        title=doc.get("title", ""),
                        content=doc.get("content", ""),
                        file_path=doc.get("file_path", ""),
                        file_type=doc.get("file_type", ""),
                        metadata=metadata,
                        score=1.0,  # No relevance score for filtered results
                    )
                )

            return SearchResponse(
                results=search_results,
                total=len(search_results),  # For filtered results, we'll use the actual count
                took=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            logger.error(f"Filter failed: {str(e)}")
            raise

    # New document operations
    async def index_single_document(self, document: Dict) -> str:
        """Index a single document.

        Args:
            document: Document to index

        Returns:
            Document ID
        """
        try:
            # Generate deterministic UUID based on file path
            doc_id = generate_uuid5(document["file_path"])

            # Index document
            self.client.data_object.create(
                data_object=document,
                class_name=self.collection,
                uuid=doc_id,
            )

            return str(doc_id)
        except Exception as e:
            logger.error(f"Failed to index document: {str(e)}")
            raise

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
        try:
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
        except Exception as e:
            logger.error(f"Failed to list documents: {str(e)}")
            raise

    async def get_document(self, document_id: str) -> Optional[Dict]:
        """Get a specific document by ID.

        Args:
            document_id: Document identifier

        Returns:
            Document metadata and content if found, None otherwise
        """
        try:
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
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {str(e)}")
            raise

    async def delete_document(self, document_id: str) -> bool:
        """Delete a specific document.

        Args:
            document_id: Document identifier

        Returns:
            True if document was deleted, False if not found
        """
        try:
            # Check if document exists
            if not await self.get_document(document_id):
                return False

            # Delete document
            self.client.data_object.delete(
                uuid=document_id,
                class_name=self.collection,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            raise
