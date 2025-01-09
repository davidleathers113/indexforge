"""Response models for the API."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Document metadata model."""

    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    author: Optional[str] = None
    size: Optional[int] = None
    extra: Optional[Dict] = None


class SearchResult(BaseModel):
    """Search result model."""

    id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    file_path: str = Field(..., description="Document file path")
    file_type: str = Field(..., description="Document file type")
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    score: float = Field(..., ge=0, le=1, description="Search relevance score")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "1234-5678",
                "title": "Machine Learning Report",
                "content": "This document discusses machine learning...",
                "file_path": "/documents/report.pdf",
                "file_type": "pdf",
                "metadata": {
                    "created_at": "2024-01-08T12:00:00Z",
                    "modified_at": "2024-01-08T12:00:00Z",
                    "author": "John Doe",
                    "size": 1024,
                    "extra": {},
                },
                "score": 0.95,
            }
        }


class SearchResponse(BaseModel):
    """Search response model."""

    results: List[SearchResult]
    total: int = Field(..., description="Total number of results")
    took: float = Field(..., description="Search time in milliseconds")

    class Config:
        json_schema_extra = {"example": {"results": [], "total": 42, "took": 123.45}}


class Stats(BaseModel):
    """API statistics model."""

    document_count: int = Field(..., description="Total number of documents")
    file_types: Dict[str, int] = Field(..., description="Document count by file type")
    status: str = Field(..., description="Collection status")

    class Config:
        json_schema_extra = {
            "example": {
                "document_count": 1000,
                "file_types": {"pdf": 500, "docx": 300, "xlsx": 200},
                "status": "active",
            }
        }
