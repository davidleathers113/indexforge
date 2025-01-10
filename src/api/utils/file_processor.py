"""File processing utilities."""

import logging
import mimetypes
from pathlib import Path
from typing import Dict, Optional

from fastapi import UploadFile

logger = logging.getLogger(__name__)

# Allowed file types and their mime types
ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt",
    "text/markdown": ".md",
    "application/json": ".json",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "text/csv": ".csv",
}

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


class FileProcessor:
    """Utility class for file operations."""

    @staticmethod
    async def save_upload(file: UploadFile, chunk_size: int = 1024 * 1024) -> Path:
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

    @staticmethod
    def determine_processor_type(file_path: Path) -> Optional[str]:
        """Determine the appropriate processor type for a file.

        Args:
            file_path: Path to the file

        Returns:
            Processor type if supported, None otherwise
        """
        suffix = file_path.suffix.lower()
        if suffix in {".xlsx", ".xls", ".csv"}:
            return "excel"
        elif suffix in {".docx", ".doc"}:
            return "word"
        return None

    @staticmethod
    async def validate_file(file: UploadFile) -> Optional[str]:
        """Validate file type and size.

        Args:
            file: File to validate

        Returns:
            Error message if validation fails, None if successful
        """
        # Check file size
        content = await file.read()
        await file.seek(0)

        if len(content) > MAX_FILE_SIZE:
            return f"File size exceeds maximum limit of {MAX_FILE_SIZE/1024/1024}MB"

        # Check file type
        mime_type = mimetypes.guess_type(file.filename)[0]
        if not mime_type or mime_type not in ALLOWED_MIME_TYPES:
            return "Invalid file type"

        return None

    @staticmethod
    def get_metadata(file: UploadFile, file_path: Path) -> Dict:
        """Get file metadata.

        Args:
            file: Uploaded file
            file_path: Path to saved file

        Returns:
            Dictionary containing file metadata
        """
        return {
            "filename": file.filename,
            "mime_type": mimetypes.guess_type(file.filename)[0],
            "size": file_path.stat().st_size,
            "extension": file_path.suffix.lower(),
        }
