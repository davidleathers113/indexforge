"""Profile router for managing user profiles."""

from fastapi import APIRouter, Depends, HTTPException, status
from supabase.client import AsyncClient

from src.api.dependencies.supabase import get_supabase_client
from src.api.middleware.rate_limit import rate_limit
from src.api.models.profiles import Profile, ProfileUpdate
from src.api.services.profile import ProfileService


router = APIRouter(prefix="/profiles", tags=["profiles"])


async def get_profile_service(
    supabase: AsyncClient = Depends(get_supabase_client),
) -> ProfileService:
    """Get an instance of the profile service.

    Args:
        supabase: Supabase client instance

    Returns:
        ProfileService instance
    """
    return ProfileService(supabase)


@router.get("/me", response_model=Profile)
@rate_limit("5/minute")  # Limit to 5 requests per minute
async def get_current_user_profile(
    profile_service: ProfileService = Depends(get_profile_service),
    supabase: AsyncClient = Depends(get_supabase_client),
) -> Profile:
    """Get the current user's profile.

    Args:
        profile_service: Profile service instance
        supabase: Supabase client instance

    Returns:
        The current user's profile

    Raises:
        HTTPException: If the user is not authenticated or profile not found
    """
    try:
        user = await supabase.auth.get_user()
        return await profile_service.get_profile(user.user.id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


@router.patch("/me", response_model=Profile)
@rate_limit("3/minute")  # Limit to 3 updates per minute
async def update_current_user_profile(
    profile_update: ProfileUpdate,
    profile_service: ProfileService = Depends(get_profile_service),
    supabase: AsyncClient = Depends(get_supabase_client),
) -> Profile:
    """Update the current user's profile.

    Args:
        profile_update: Profile update data
        profile_service: Profile service instance
        supabase: Supabase client instance

    Returns:
        The updated profile

    Raises:
        HTTPException: If the user is not authenticated or update fails
    """
    try:
        user = await supabase.auth.get_user()
        return await profile_service.update_profile(user.user.id, profile_update)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


@router.get("/{user_id}", response_model=Profile)
@rate_limit("10/minute")  # Limit to 10 requests per minute
async def get_user_profile(
    user_id: str,
    profile_service: ProfileService = Depends(get_profile_service),
) -> Profile:
    """Get a user's profile by ID.

    Args:
        user_id: The ID of the user
        profile_service: Profile service instance

    Returns:
        The user's profile

    Raises:
        HTTPException: If the profile is not found
    """
    return await profile_service.get_profile(user_id)
