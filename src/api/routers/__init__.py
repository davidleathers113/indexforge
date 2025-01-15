"""API routers package initialization.

This package contains FastAPI routers for different API endpoints.
"""

from src.api.routers.health import router as health_router

__all__ = ["health_router"]
