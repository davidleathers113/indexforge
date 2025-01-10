"""FastAPI application entry point."""

import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk import configure_scope

from src.api.config.sentry import init_sentry
from src.api.config.settings import settings
from src.api.routers import search_router
from src.api.routers.auth import router as auth_router
from src.api.routers.document import router as document_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Sentry with our comprehensive configuration
init_sentry()

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for document operations",
    version=settings.VERSION,
    docs_url=f"{settings.API_V1_STR}/docs",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_sentry_context(request: Request, call_next):
    """Add user and context information to Sentry events."""
    with configure_scope() as scope:
        # Add request context
        scope.set_tag("endpoint", request.url.path)
        scope.set_tag("method", request.method)

        # Add user context if available
        if hasattr(request.state, "user"):
            scope.set_user(
                {
                    "id": request.state.user.id,
                    "email": request.state.user.email,
                    "tenant_id": request.state.user.tenant_id,
                }
            )

        # Add additional context
        scope.set_context(
            "request_info",
            {
                "client_host": request.client.host if request.client else None,
                "path_params": dict(request.path_params),
                "query_params": dict(request.query_params),
            },
        )

    try:
        response = await call_next(request)
        return response
    except Exception as e:
        with configure_scope() as scope:
            scope.set_tag("error_type", type(e).__name__)
        raise


# Include routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(document_router, prefix=settings.API_V1_STR)
app.include_router(search_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.VERSION}


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
