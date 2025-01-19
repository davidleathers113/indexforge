"""Authentication router package."""

from fastapi import APIRouter

from .oauth_routes import router as oauth_router
from .token_routes import router as token_router
from .user_routes import router as user_router


# Create main auth router
router = APIRouter(prefix="/auth", tags=["auth"])

# Include sub-routers
router.include_router(token_router)
router.include_router(user_router)
router.include_router(oauth_router)
