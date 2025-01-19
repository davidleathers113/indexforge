"""Health check router.

This module provides endpoints for system health monitoring.
"""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from src.core import CacheService, Container, VectorService


router = APIRouter(tags=["Health"])


@router.get("/health")
@inject
async def health_check(
    cache: CacheService = Depends(Provide[Container.cache]),
    vector_db: VectorService = Depends(Provide[Container.vector_db]),
) -> dict:
    """Check system health.

    This endpoint verifies the health of all system components
    including Redis and Weaviate connections.

    Returns:
        dict: Health status of all components
    """
    status = {"status": "healthy", "components": {"cache": "healthy", "vector_db": "healthy"}}

    try:
        await cache.get("health_check")
    except Exception:
        status["components"]["cache"] = "unhealthy"
        status["status"] = "degraded"

    try:
        await vector_db.get_object("Test", "00000000-0000-0000-0000-000000000000")
    except Exception:
        status["components"]["vector_db"] = "unhealthy"
        status["status"] = "degraded"

    return status
