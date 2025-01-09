"""Document service for handling file uploads and indexing."""

import logging
from pathlib import Path
from typing import BinaryIO, Dict, List, Optional

from fastapi import UploadFile

from src.api.models.requests import DocumentUploadResponse
from src.api.repositories.weaviate_repo import WeaviateRepository
from src.connectors.direct_documentation_indexing import (
    DocumentConnector,
    ExcelProcessor,
    WordProcessor,
)

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for document operations."""

    def __init__(self, repository: WeaviateRepository):
        """Initialize service with repository.

        Args:
            repository: Repository for data access
        """
        self._repository = repository
        self._connector = self._setup_connector()

    def _setup_connector(self) -> DocumentConnector:
        """Set up document connector with processors."""
        connector = DocumentConnector()

        # Configure processors
        excel_config = {
            "max_rows": None,
            "required_columns": [],
            "skip_sheets": [],
        }

        word_config = {
            "extract_headers": True,
            "extract_tables": True,
            "extract_images": False,
        }

        connector.processors = {
            "excel": ExcelProcessor(excel_config),
            "word": WordProcessor(word_config),
        }

        return connector

    async def _save_upload(self, file: UploadFile, chunk_size: int = 1024 * 1024) -> Path:
        """Save uploaded file with chunked writing.

        Args:
            file: Uploaded file
            chunk_size: Size of chunks to read/write in bytes (default: 1MB)

        Returns:
            Path to saved temporary file
        """
        temp_path = Path(f"/tmp/{file.filename}")
        with temp_path.open("wb") as buffer:
            while chunk := await file.read(chunk_size):
                buffer.write(chunk)
        return temp_path

    def _process_file_content(self, file_path: Path, file_stream: BinaryIO) -> dict:
        """Process file content with appropriate processor.

        Args:
            file_path: Path to the file
            file_stream: File stream for reading

        Returns:
            Dict containing processing results
        """
        suffix = file_path.suffix.lower()
        processor_type = (
            "excel"
            if suffix in {".xlsx", ".xls", ".csv"}
            else "word" if suffix in {".docx", ".doc"} else None
        )

        if not processor_type or processor_type not in self._connector.processors:
            return {"status": "error", "error": f"Unsupported file type: {suffix}"}

        return self._connector.process_file(file_path)

    async def process_upload(self, file: UploadFile) -> DocumentUploadResponse:
        """Process single file upload.

        Args:
            file: Uploaded file

        Returns:
            DocumentUploadResponse with processing status
        """
        temp_path = None
        try:
            # Save file with chunked writing
            temp_path = await self._save_upload(file)

            # Process file content
            with temp_path.open("rb") as file_stream:
                result = self._process_file_content(temp_path, file_stream)

            if result["status"] == "error":
                return DocumentUploadResponse(
                    file_name=file.filename,
                    file_type=temp_path.suffix.lower(),
                    status="error",
                    message=result["error"],
                )

            # Prepare document for indexing
            doc = {
                "title": file.filename,
                "content": result["content"],
                "file_path": file.filename,  # Use filename as path for uploaded files
                "file_type": temp_path.suffix.lower(),
                "metadata": result.get("metadata", {}),
            }

            # Index document
            document_id = await self._repository.index_single_document(doc)

            return DocumentUploadResponse(
                file_name=file.filename,
                file_type=temp_path.suffix.lower(),
                status="success",
                message="Document successfully indexed",
                document_id=document_id,
            )

        except Exception as e:
            logger.error(f"Failed to process upload {file.filename}: {str(e)}")
            return DocumentUploadResponse(
                file_name=file.filename,
                file_type=getattr(file, "content_type", "unknown"),
                status="error",
                message=f"Processing failed: {str(e)}",
            )

        finally:
            # Clean up temporary file
            if temp_path and temp_path.exists():
                temp_path.unlink()

    async def process_batch_upload(self, files: List[UploadFile]) -> List[DocumentUploadResponse]:
        """Process multiple file uploads in batch.

        Args:
            files: List of uploaded files

        Returns:
            List of DocumentUploadResponse for each file
        """
        results = []
        for file in files:
            result = await self.process_upload(file)
            results.append(result)
        return results

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
        return await self._repository.list_documents(
            file_type=file_type,
            limit=limit,
            offset=offset,
        )

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

    async def get_stats(self) -> Dict:
        """Get document collection statistics.

        Returns:
            Statistics about indexed documents
        """
        return await self._repository.get_stats()
