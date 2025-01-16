"""Request models for the API."""

from enum import Enum

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class OAuthProvider(str, Enum):
    """OAuth provider enum."""

    GOOGLE = "google"
    GITHUB = "github"


class OAuthRequest(BaseModel):
    """OAuth request model."""

    provider: OAuthProvider = Field(..., description="OAuth provider")
    redirect_to: HttpUrl | None = Field(
        None, description="URL to redirect to after authentication"
    )

    class Config:
        json_schema_extra = {
            "example": {"provider": "google", "redirect_to": "http://localhost:3000/dashboard"}
        }


class OAuthCallback(BaseModel):
    """OAuth callback model."""

    code: str = Field(..., description="OAuth authorization code")
    state: str | None = Field(None, description="State parameter for CSRF protection")
    provider: OAuthProvider = Field(..., description="OAuth provider")

    class Config:
        json_schema_extra = {
            "example": {"code": "4/0AeaYSHDM...", "state": "xyz123", "provider": "google"}
        }


class SearchQuery(BaseModel):
    """Search query model."""

    query: str = Field(..., description="Search query text")
    limit: int | None = Field(10, ge=1, le=100, description="Maximum number of results")
    offset: int | None = Field(0, ge=0, description="Number of results to skip")

    class Config:
        json_schema_extra = {"example": {"query": "machine learning", "limit": 10, "offset": 0}}


class DocumentFilter(BaseModel):
    """Document filter model."""

    file_type: str | None = Field(None, description="Filter by file type")
    date_from: str | None = Field(None, description="Filter by date from (ISO format)")
    date_to: str | None = Field(None, description="Filter by date to (ISO format)")

    class Config:
        json_schema_extra = {
            "example": {"file_type": "pdf", "date_from": "2024-01-01", "date_to": "2024-12-31"}
        }


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""

    file_name: str = Field(..., description="Name of the uploaded file")
    file_type: str = Field(..., description="Type of the uploaded file")
    status: str = Field(..., description="Upload status (success/error)")
    message: str | None = Field(None, description="Additional status message or error details")
    document_id: str | None = Field(None, description="ID of the indexed document if successful")

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


class SignUpRequest(BaseModel):
    """Sign up request model."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password")
    name: str | None = Field(None, description="User's full name")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "name": "John Doe",
            }
        }


class SignInRequest(BaseModel):
    """Sign in request model."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

    class Config:
        json_schema_extra = {"example": {"email": "user@example.com", "password": "SecurePass123!"}}


class PasswordResetRequest(BaseModel):
    """Password reset request model."""

    email: EmailStr = Field(..., description="User's email address")

    class Config:
        json_schema_extra = {"example": {"email": "user@example.com"}}
