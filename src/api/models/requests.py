"""Request models for the API."""

from typing import Optional

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """Search query model."""

    query: str = Field(..., description="Search query text")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Maximum number of results")
    offset: Optional[int] = Field(0, ge=0, description="Number of results to skip")

    class Config:
        json_schema_extra = {"example": {"query": "machine learning", "limit": 10, "offset": 0}}


class DocumentFilter(BaseModel):
    """Document filter model."""

    file_type: Optional[str] = Field(None, description="Filter by file type")
    date_from: Optional[str] = Field(None, description="Filter by date from (ISO format)")
    date_to: Optional[str] = Field(None, description="Filter by date to (ISO format)")

    class Config:
        json_schema_extra = {
            "example": {"file_type": "pdf", "date_from": "2024-01-01", "date_to": "2024-12-31"}
        }


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""

    file_name: str = Field(..., description="Name of the uploaded file")
    file_type: str = Field(..., description="Type of the uploaded file")
    status: str = Field(..., description="Upload status (success/error)")
    message: Optional[str] = Field(None, description="Additional status message or error details")
    document_id: Optional[str] = Field(None, description="ID of the indexed document if successful")

    class Config:
        json_schema_extra = {
            "example": {
                "file_name": "report.docx",
                "file_type": "docx",
                "status": "success",
                "message": "Document successfully indexed",
                "document_id": "1234-5678",
            }
        }
