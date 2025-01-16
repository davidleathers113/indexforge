"""Response builder utilities."""


from src.api.models.requests import DocumentUploadResponse


class ResponseBuilder:
    """Utility class for building response objects."""

    @staticmethod
    def document_upload_success(
        filename: str,
        file_type: str,
        document_id: str,
        message: str = "Document successfully indexed",
    ) -> DocumentUploadResponse:
        """Build a successful document upload response.

        Args:
            filename: Name of the uploaded file
            file_type: Type/extension of the file
            document_id: ID of the indexed document
            message: Optional success message

        Returns:
            DocumentUploadResponse for successful upload
        """
        return DocumentUploadResponse(
            file_name=filename,
            file_type=file_type,
            status="success",
            message=message,
            document_id=document_id,
        )

    @staticmethod
    def document_upload_error(
        filename: str, error_message: str, file_type: str | None = None
    ) -> DocumentUploadResponse:
        """Build an error document upload response.

        Args:
            filename: Name of the uploaded file
            error_message: Error message describing the failure
            file_type: Optional type/extension of the file

        Returns:
            DocumentUploadResponse for failed upload
        """
        return DocumentUploadResponse(
            file_name=filename,
            file_type=file_type or "unknown",
            status="error",
            message=error_message,
            document_id=None,
        )
