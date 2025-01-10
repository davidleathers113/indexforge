"""File upload service for handling file uploads and processing."""

import logging
from typing import List

from fastapi import UploadFile

from src.api.models.requests import DocumentUploadResponse
from src.api.repositories.weaviate_repo import WeaviateRepository
from src.api.services.connector_service import ConnectorService
from src.api.services.virus_scan import VirusScanService
from src.api.utils.file_processor import FileProcessor
from src.api.utils.response_builder import ResponseBuilder

logger = logging.getLogger(__name__)


class FileUploadService:
    """Handles file upload and processing."""

    def __init__(self, repository: WeaviateRepository):
        """Initialize the file upload service.

        Args:
            repository: Repository for data access
        """
        self._repository = repository
        self._virus_scan = VirusScanService()
        self._file_processor = FileProcessor()
        self._connector = ConnectorService.setup_connector()
        self._response_builder = ResponseBuilder()

    async def process_upload(self, file: UploadFile) -> DocumentUploadResponse:
        """Process a single file upload.

        Args:
            file: File to upload and process

        Returns:
            Upload response with status
        """
        temp_path = None
        try:
            if error_msg := await self._file_processor.validate_file(file):
                return self._response_builder.document_upload_error(file.filename, error_msg)

            if not await self._virus_scan.scan_file(file):
                return self._response_builder.document_upload_error(
                    file.filename, "File failed security scan"
                )

            temp_path = await self._file_processor.save_upload(file)
            processor_type = self._file_processor.determine_processor_type(temp_path)

            if not processor_type or processor_type not in self._connector.processors:
                return self._response_builder.document_upload_error(
                    file.filename, f"Unsupported file type: {temp_path.suffix}"
                )

            result = self._connector.process_file(temp_path)

            if result["status"] == "error":
                return self._response_builder.document_upload_error(
                    file.filename, result["error"], temp_path.suffix.lower()
                )

            metadata = self._file_processor.get_metadata(file, temp_path)
            metadata.update(result.get("metadata", {}))

            document_id = await self._repository.index_single_document(
                {
                    "title": file.filename,
                    "content": result["content"],
                    "file_path": file.filename,
                    "file_type": temp_path.suffix.lower(),
                    "metadata": metadata,
                }
            )

            return self._response_builder.document_upload_success(
                file.filename, temp_path.suffix.lower(), document_id
            )

        except Exception as e:
            logger.error(f"Failed to process upload {file.filename}: {str(e)}")
            return self._response_builder.document_upload_error(file.filename, str(e))

        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink()

    async def process_batch_upload(self, files: List[UploadFile]) -> List[DocumentUploadResponse]:
        """Process multiple file uploads.

        Args:
            files: List of files to upload and process

        Returns:
            List of upload responses
        """
        return [await self.process_upload(file) for file in files]
