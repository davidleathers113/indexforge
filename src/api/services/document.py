"""Document service for orchestrating document operations."""

import logging
from typing import Dict, List, Optional

from fastapi import UploadFile
from fastapi.responses import StreamingResponse

from src.api.models.requests import DocumentUploadResponse
from src.api.repositories.weaviate_repo import WeaviateRepository
from src.api.services.document_retrieval_service import DocumentRetrievalService
from src.api.services.file_upload_service import FileUploadService
from src.api.services.statistics_service import StatisticsService

logger = logging.getLogger(__name__)


class DocumentService:
    """High-level orchestration for document operations."""

    def __init__(self, repository: WeaviateRepository):
        """Initialize document service with specialized services.

        Args:
            repository: Repository for data access
        """
        self._repository = repository
        self._upload_service = FileUploadService(repository)
        self._retrieval_service = DocumentRetrievalService(repository)
        self._stats_service = StatisticsService(repository)

    async def process_upload(self, file: UploadFile) -> DocumentUploadResponse:
        """Process single file upload.

        Args:
            file: File to upload

        Returns:
            Upload response with status
        """
        return await self._upload_service.process_upload(file)

    async def process_batch_upload(self, files: List[UploadFile]) -> List[DocumentUploadResponse]:
        """Process multiple file uploads.

        Args:
            files: List of files to upload

        Returns:
            List of upload responses
        """
        return await self._upload_service.process_batch_upload(files)

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
        return await self._retrieval_service.list_documents(file_type, limit, offset)

    async def get_document(self, document_id: str) -> Optional[Dict]:
        """Get a specific document by ID.

        Args:
            document_id: Document identifier

        Returns:
            Document metadata and content if found
        """
        return await self._retrieval_service.get_document(document_id)

    async def delete_document(self, document_id: str) -> bool:
        """Delete a specific document.

        Args:
            document_id: Document identifier

        Returns:
            True if deleted successfully
        """
        return await self._retrieval_service.delete_document(document_id)

    async def get_stats(self) -> dict:
        """Get document collection statistics.

        Returns:
            Collection statistics
        """
        return await self._stats_service.get_stats()

    async def download_document(self, document_id: str) -> StreamingResponse:
        """Download a document securely.

        Args:
            document_id: Document identifier

        Returns:
            StreamingResponse for secure file download
        """
        return await self._retrieval_service.download_document(document_id)
