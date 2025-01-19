"""File processor utilities.

This module provides utilities for handling file uploads and processing.
"""

import logging
import mimetypes
from pathlib import Path
from typing import Any, Dict

from fastapi import UploadFile

logger = logging.getLogger(__name__)


class FileProcessor:
    """Utility class for file operations."""

    ALLOWED_MIME_TYPES = {
        "application/pdf": "pdf",
        "application/msword": "doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/vnd.ms-excel": "xls",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
        "text/plain": "txt",
        "text/markdown": "md",
        "text/csv": "csv",
    }

    @staticmethod
    async def save_upload(file: UploadFile, chunk_size: int = 1024 * 1024) -> Path:
        """Save an uploaded file to disk.

        Args:
            file: The uploaded file
            chunk_size: Size of chunks to read/write in bytes (default: 1MB)

        Returns:
            Path to the saved file

        Raises:
            IOError: If file saving fails
        """
        try:
            temp_file = Path(f"/tmp/{file.filename}")
            with temp_file.open("wb") as f:
                while chunk := await file.read(chunk_size):
                    f.write(chunk)
            logger.info("Successfully saved file: %s", temp_file)
            return temp_file
        except Exception as e:
            logger.error("Failed to save file %s: %s", file.filename, str(e))
            raise IOError(f"Failed to save file: {str(e)}") from e

    @staticmethod
    def determine_processor_type(file_path: Path) -> str | None:
        """Determine the appropriate processor type for a file.

        Args:
            file_path: Path to the file

        Returns:
            Processor type string or None if not supported
        """
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type in FileProcessor.ALLOWED_MIME_TYPES:
            return FileProcessor.ALLOWED_MIME_TYPES[mime_type]
        logger.warning("Unsupported file type: %s", mime_type)
        return None

    @staticmethod
    async def validate_file(file: UploadFile) -> str | None:
        """Validate an uploaded file.

        Args:
            file: The uploaded file

        Returns:
            Error message if validation fails, None if successful
        """
        if not file.filename:
            return "No filename provided"

        mime_type = file.content_type
        if mime_type not in FileProcessor.ALLOWED_MIME_TYPES:
            return f"Unsupported file type: {mime_type}"

        try:
            size = 0
            while chunk := await file.read(8192):
                size += len(chunk)
                if size > 100 * 1024 * 1024:  # 100MB limit
                    return "File too large (max 100MB)"
            await file.seek(0)
            return None
        except Exception as e:
            logger.error("File validation failed: %s", str(e))
            return f"File validation failed: {str(e)}"

    @staticmethod
    def get_metadata(file: UploadFile, file_path: Path) -> Dict[str, Any]:
        """Get metadata for a file.

        Args:
            file: The uploaded file
            file_path: Path to the saved file

        Returns:
            Dictionary containing file metadata
        """
        mime_type, encoding = mimetypes.guess_type(str(file_path))
        stats = file_path.stat()

        return {
            "filename": file.filename,
            "size": stats.st_size,
            "mime_type": mime_type or "application/octet-stream",
            "encoding": encoding,
            "created_at": stats.st_ctime,
            "modified_at": stats.st_mtime,
            "processor_type": FileProcessor.determine_processor_type(file_path),
        }
