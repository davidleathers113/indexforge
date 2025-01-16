"""Profile service for managing user profiles."""


from fastapi import HTTPException, status
from supabase.client import AsyncClient

from src.api.models.profiles import Profile, ProfileUpdate


class ProfileService:
    """Service for managing user profiles."""

    def __init__(self, supabase: AsyncClient):
        """Initialize the profile service.

        Args:
            supabase: Supabase client instance
        """
        self._supabase = supabase

    async def create_profile(self, user_id: str, profile_data: dict) -> Profile:
        """Create a new user profile.

        Args:
            user_id: The ID of the user
            profile_data: The profile data to create

        Returns:
            The created profile

        Raises:
            HTTPException: If the profile creation fails
        """
        try:
            response = (
                await self._supabase.table("profiles")
                .insert(
                    {
                        "id": user_id,
                        **profile_data,
                    }
                )
                .single()
            )

            if not response:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create profile",
                )

            return Profile.model_validate(response)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    async def get_profile(self, user_id: str) -> Profile:
        """Get a user's profile.

        Args:
            user_id: The ID of the user

        Returns:
            The user's profile

        Raises:
            HTTPException: If the profile is not found
        """
        try:
            response = await self._supabase.table("profiles").select("*").eq("id", user_id).single()
            if not response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Profile not found for user {user_id}",
                )
            return Profile.model_validate(response)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    async def update_profile(self, user_id: str, profile_update: ProfileUpdate) -> Profile:
        """Update a user's profile.

        Args:
            user_id: The ID of the user
            profile_update: The profile update data

        Returns:
            The updated profile

        Raises:
            HTTPException: If the profile update fails
        """
        try:
            response = (
                await self._supabase.table("profiles")
                .update(profile_update.model_dump(exclude_unset=True))
                .eq("id", user_id)
                .single()
            )

            if not response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Profile not found for user {user_id}",
                )

            return Profile.model_validate(response)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def delete_profile(self, user_id: str) -> None:
        """Delete a user's profile.

        Args:
            user_id: The ID of the user

        Raises:
            HTTPException: If the profile deletion fails
        """
        try:
            await self._supabase.table("profiles").delete().eq("id", user_id).execute()
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
