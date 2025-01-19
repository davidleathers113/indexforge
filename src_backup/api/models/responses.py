"""Response models for the API."""

from typing import Any

from pydantic import BaseModel, EmailStr, Field


class DocumentMetadata(BaseModel):
    """Document metadata model."""

    created_at: str | None = None
    modified_at: str | None = None
    author: str | None = None
    size: int | None = None
    extra: dict | None = None


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

    results: list[SearchResult]
    total: int = Field(..., description="Total number of results")
    took: float = Field(..., description="Search time in milliseconds")

    class Config:
        json_schema_extra = {"example": {"results": [], "total": 42, "took": 123.45}}


class Stats(BaseModel):
    """API statistics model."""

    document_count: int = Field(..., description="Total number of documents")
    file_types: dict[str, int] = Field(..., description="Document count by file type")
    status: str = Field(..., description="Collection status")

    class Config:
        json_schema_extra = {
            "example": {
                "document_count": 1000,
                "file_types": {"pdf": 500, "docx": 300, "xlsx": 200},
                "status": "active",
            }
        }


class AuthResponse(BaseModel):
    """Authentication response model."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    user: dict[str, Any] = Field(..., description="User data from Supabase")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "name": "John Doe",
                    "created_at": "2024-01-10T00:00:00Z",
                },
            }
        }


class UserProfile(BaseModel):
    """User profile response model."""

    id: str = Field(..., description="User's unique identifier")
    email: EmailStr = Field(..., description="User's email address")
    name: str | None = Field(None, description="User's full name")
    created_at: str = Field(..., description="Account creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "name": "John Doe",
                "created_at": "2024-01-10T00:00:00Z",
            }
        }
