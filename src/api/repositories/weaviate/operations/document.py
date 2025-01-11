"""Weaviate document operations."""

import json
from typing import Dict, List, Optional

from weaviate.util import generate_uuid5

from src.api.errors.weaviate_error_handling import with_weaviate_error_handling
from src.api.repositories.weaviate.base import BaseWeaviateRepository


class DocumentRepository(BaseWeaviateRepository):
    """Repository for document operations."""

    @with_weaviate_error_handling
    async def create_document(self, document: Dict) -> str:
        """Create a new document.

        Args:
            document: Document data to create

        Returns:
            Document ID
        """
        # Generate deterministic UUID based on file path
        doc_id = generate_uuid5(document["file_path"])

        # Validate document schema
        self._validate_document(document)

        # Create document
        self.collection_ref.data.create(
            data_object=document,
            uuid=doc_id,
        )

        return str(doc_id)

    @with_weaviate_error_handling
    async def get_document(self, document_id: str) -> Optional[Dict]:
        """Get document by ID.

        Args:
            document_id: Document ID to retrieve

        Returns:
            Document if found, None otherwise
        """
        result = (
            self.collection_ref.query.fetch_objects(
                ["title", "content", "file_path", "file_type", "metadata_json"]
            )
            .with_where({"path": ["id"], "operator": "Equal", "valueString": document_id})
            .with_limit(1)
            .do()
        )

        if not result.objects:
            return None

        obj = result.objects[0]
        metadata = json.loads(obj.properties.get("metadata_json", "{}"))

        return {
            "id": obj.id,
            "title": obj.properties.get("title", ""),
            "content": obj.properties.get("content", ""),
            "file_path": obj.properties.get("file_path", ""),
            "file_type": obj.properties.get("file_type", ""),
            "metadata": metadata,
        }

    @with_weaviate_error_handling
    async def update_document(self, document_id: str, document: Dict) -> bool:
        """Update existing document.

        Args:
            document_id: Document ID to update
            document: Updated document data

        Returns:
            True if updated, False if not found
        """
        # Check if document exists
        if not await self.get_document(document_id):
            return False

        # Validate document schema
        self._validate_document(document)

        # Update document
        self.collection_ref.data.update(
            data_object=document,
            uuid=document_id,
        )

        return True

    @with_weaviate_error_handling
    async def delete_document(self, document_id: str) -> bool:
        """Delete document by ID.

        Args:
            document_id: Document ID to delete

        Returns:
            True if deleted, False if not found
        """
        # Check if document exists
        if not await self.get_document(document_id):
            return False

        # Delete document
        self.collection_ref.data.delete(
            uuid=document_id,
        )

        return True

    @with_weaviate_error_handling
    async def list_documents(
        self,
        file_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict]:
        """List documents with optional filtering.

        Args:
            file_type: Optional file type filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of documents
        """
        # Build query
        query = self.collection_ref.query.fetch_objects(
            ["title", "file_path", "file_type", "metadata_json"]
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

        # Format results
        documents = []
        for obj in result.objects:
            metadata = json.loads(obj.properties.get("metadata_json", "{}"))
            documents.append(
                {
                    "id": obj.id,
                    "title": obj.properties.get("title", ""),
                    "file_path": obj.properties.get("file_path", ""),
                    "file_type": obj.properties.get("file_type", ""),
                    "metadata": metadata,
                }
            )

        return documents

    def _validate_document(self, document: Dict) -> None:
        """Validate document schema.

        Args:
            document: Document to validate

        Raises:
            ValueError: If document is invalid
        """
        required_fields = ["title", "content", "file_path", "file_type"]
        for field in required_fields:
            if field not in document:
                raise ValueError(f"Missing required field: {field}")

        if not isinstance(document.get("metadata_json", "{}"), str):
            raise ValueError("metadata_json must be a JSON string")
