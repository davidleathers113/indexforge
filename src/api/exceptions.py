"""Custom exceptions for the API."""

from fastapi import HTTPException, status


class DocumentException(HTTPException):
    """Base exception for document-related errors."""

    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        """Initialize the exception.

        Args:
            detail: Error message
            status_code: HTTP status code
        """
        super().__init__(status_code=status_code, detail=detail)


class DocumentNotFoundError(DocumentException):
    """Exception raised when a document is not found."""

    def __init__(self, document_id: str):
        """Initialize the exception.

        Args:
            document_id: ID of the document that was not found
        """
        super().__init__(
            detail=f"Document not found: {document_id}",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class FileProcessingError(DocumentException):
    """Exception raised when file processing fails."""

    def __init__(self, filename: str, reason: str):
        """Initialize the exception.

        Args:
            filename: Name of the file that failed processing
            reason: Reason for the failure
        """
        super().__init__(
            detail=f"Failed to process file {filename}: {reason}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class SecurityScanError(DocumentException):
    """Exception raised when security scan fails."""

    def __init__(self, filename: str):
        """Initialize the exception.

        Args:
            filename: Name of the file that failed security scan
        """
        super().__init__(
            detail=f"File {filename} failed security scan",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class UnsupportedFileTypeError(DocumentException):
    """Exception raised when file type is not supported."""

    def __init__(self, filename: str, file_type: str):
        """Initialize the exception.

        Args:
            filename: Name of the file
            file_type: Unsupported file type
        """
        super().__init__(
            detail=f"Unsupported file type for {filename}: {file_type}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class FileSizeLimitExceededError(DocumentException):
    """Exception raised when file size exceeds limit."""

    def __init__(self, filename: str, size: int, limit: int):
        """Initialize the exception.

        Args:
            filename: Name of the file
            size: Actual file size in bytes
            limit: Size limit in bytes
        """
        super().__init__(
            detail=(
                f"File {filename} size ({size/1024/1024:.1f}MB) "
                f"exceeds limit of {limit/1024/1024:.1f}MB"
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class DocumentContentNotFoundError(DocumentException):
    """Exception raised when document content is not found."""

    def __init__(self, document_id: str):
        """Initialize the exception.

        Args:
            document_id: ID of the document whose content was not found
        """
        super().__init__(
            detail=f"Document content not found: {document_id}",
            status_code=status.HTTP_404_NOT_FOUND,
        )
