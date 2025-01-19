"""Main FastAPI application module.

This module initializes and configures the FastAPI application,
setting up middleware, routers, and dependency injection.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import health_router
from src.core import Container, get_settings


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    settings = get_settings()
    container = Container()

    app = FastAPI(title=settings.api_title, version=settings.api_version, debug=settings.debug)

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_router, prefix="/api/v1")

    # Wire container
    container.wire(modules=["src.api.routers"])

    @app.on_event("startup")
    async def startup() -> None:
        """Initialize services on startup."""
        pass

    @app.on_event("shutdown")
    async def shutdown() -> None:
        """Clean up services on shutdown."""
        container.cache().close()
        container.vector_db().close()

    return app


app = create_app()
