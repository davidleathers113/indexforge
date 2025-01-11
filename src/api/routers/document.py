"""Document router for API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, UploadFile
from fastapi.responses import StreamingResponse

from src.api.dependencies.weaviate import get_weaviate_client
from src.api.models.requests import DocumentUploadResponse
from src.api.repositories.weaviate_repo import WeaviateRepository
from src.api.services.document import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_service(
    client=Depends(get_weaviate_client),
) -> DocumentService:
    """Dependency injection for document service."""
    repository = WeaviateRepository(client)
    return DocumentService(repository)


@router.get("/", response_model=List[dict])
async def list_documents(
    file_type: Optional[str] = Query(None, description="Filter by file type (e.g., docx, pdf)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of documents to return"),
    offset: int = Query(0, ge=0, description="Number of documents to skip"),
    service: DocumentService = Depends(get_document_service),
) -> List[dict]:
    """List indexed documents with optional filtering.

    Args:
        file_type: Optional file type filter
        limit: Maximum number of results (default: 10)
        offset: Number of results to skip (default: 0)
        service: Injected document service

    Returns:
        List of document metadata
    """
    try:
        return await service.list_documents(file_type=file_type, limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=dict)
async def get_document(
    document_id: str = Path(..., description="The ID of the document to retrieve"),
    service: DocumentService = Depends(get_document_service),
) -> dict:
    """Get a specific document by ID.

    Args:
        document_id: Document identifier
        service: Injected document service

    Returns:
        Document metadata and content
    """
    try:
        doc = await service.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
) -> DocumentUploadResponse:
    """Upload and index a single document.

    Args:
        file: Document file to upload
        service: Injected document service

    Returns:
        DocumentUploadResponse containing upload/indexing status
    """
    try:
        return await service.process_upload(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/batch", response_model=List[DocumentUploadResponse])
async def upload_documents(
    files: List[UploadFile] = File(...),
    service: DocumentService = Depends(get_document_service),
) -> List[DocumentUploadResponse]:
    """Upload and index multiple documents.

    Args:
        files: List of document files to upload
        service: Injected document service

    Returns:
        List of DocumentUploadResponse for each file
    """
    try:
        return await service.process_batch_upload(files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(
    document_id: str = Path(..., description="The ID of the document to delete"),
    service: DocumentService = Depends(get_document_service),
) -> dict:
    """Delete a specific document.

    Args:
        document_id: Document identifier
        service: Injected document service

    Returns:
        Deletion status
    """
    try:
        success = await service.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"status": "success", "message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_document_stats(
    service: DocumentService = Depends(get_document_service),
) -> dict:
    """Get document collection statistics.

    Returns:
        Statistics about indexed documents
    """
    try:
        return await service.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/download")
async def download_document(
    document_id: str = Path(..., description="The ID of the document to download"),
    service: DocumentService = Depends(get_document_service),
) -> StreamingResponse:
    """Download a specific document.

    Args:
        document_id: Document identifier
        service: Injected document service

    Returns:
        Streaming response for secure file download
    """
    try:
        return await service.download_document(document_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
