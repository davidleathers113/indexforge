"""Search router for API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies.weaviate import get_weaviate_client
from src.api.models.requests import DocumentFilter, SearchQuery
from src.api.models.responses import SearchResponse, Stats
from src.api.repositories.weaviate_repo import WeaviateRepository
from src.api.services.search import SearchService

router = APIRouter(prefix="/search", tags=["search"])


def get_search_service(
    client=Depends(get_weaviate_client),
) -> SearchService:
    """Dependency injection for search service."""
    repository = WeaviateRepository(client)
    return SearchService(repository)


@router.post("", response_model=SearchResponse)
async def search_documents(
    query: SearchQuery,
    filter_params: Optional[DocumentFilter] = None,
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    """Search documents with semantic search and optional filtering.

    Args:
        query: Search parameters
        filter_params: Optional filter criteria
        service: Injected search service

    Returns:
        SearchResponse containing results and metadata
    """
    try:
        return await service.search_documents(query, filter_params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=Stats)
async def get_stats(
    service: SearchService = Depends(get_search_service),
) -> Stats:
    """Get collection statistics.

    Args:
        service: Injected search service

    Returns:
        Stats containing document counts and status
    """
    try:
        return await service.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
