"""Document retrieval service for handling document operations."""

import logging
import mimetypes
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse

from src.api.repositories.weaviate_repo import WeaviateRepository

logger = logging.getLogger(__name__)


class DocumentRetrievalService:
    """Handles document retrieval and deletion."""

    def __init__(self, repository: WeaviateRepository):
        """Initialize the document retrieval service.

        Args:
            repository: Repository for data access
        """
        self._repository = repository

    async def list_documents(self, file_type: Optional[str], limit: int, offset: int) -> List[Dict]:
        """List indexed documents with optional filtering.

        Args:
            file_type: Optional file type filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of document metadata
        """
        return await self._repository.list_documents(file_type, limit, offset)

    async def get_document(self, document_id: str) -> Optional[Dict]:
        """Get a specific document by ID.

        Args:
            document_id: Document identifier

        Returns:
            Document metadata and content if found, None otherwise
        """
        return await self._repository.get_document(document_id)

    async def delete_document(self, document_id: str) -> bool:
        """Delete a specific document.

        Args:
            document_id: Document identifier

        Returns:
            True if document was deleted, False if not found
        """
        return await self._repository.delete_document(document_id)

    async def download_document(self, document_id: str) -> StreamingResponse:
        """Download a document securely.

        Args:
            document_id: Document identifier

        Returns:
            StreamingResponse for secure file download

        Raises:
            HTTPException: If document not found or access denied
        """
        doc = await self.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

        content = await self._repository.get_document_content(document_id)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document content not found"
            )

        mime_type = mimetypes.guess_type(doc["file_path"])[0] or "application/octet-stream"
        return StreamingResponse(
            content=iter([content]),
            media_type=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{doc["title"]}"',
                "Content-Type": mime_type,
            },
        )
