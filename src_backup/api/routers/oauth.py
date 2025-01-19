"""OAuth authentication router."""


from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from supabase.client import AsyncClient

from src.api.dependencies.supabase import get_supabase_client
from src.api.middleware.rate_limit import rate_limit
from src.api.services.profile import ProfileService


router = APIRouter(prefix="/auth", tags=["oauth"])


@router.get("/google")
@rate_limit("10/minute")
async def google_oauth_init(
    request: Request,
    redirect_to: str = Query(..., description="URL to redirect after successful authentication"),
    supabase: AsyncClient = Depends(get_supabase_client),
) -> dict[str, str]:
    """Initialize Google OAuth flow.

    Args:
        request: The incoming request
        redirect_to: URL to redirect after successful authentication
        supabase: Supabase client instance

    Returns:
        Dict containing the authorization URL
    """
    try:
        # Get the OAuth URL from Supabase
        auth_url = await supabase.auth.get_sign_in_with_oauth_url(
            "google",
            {
                "redirectTo": redirect_to,
                "scopes": "email profile",
            },
        )
        return {"authorization_url": auth_url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize Google OAuth: {e!s}",
        )


@router.get("/github")
@rate_limit("10/minute")
async def github_oauth_init(
    request: Request,
    redirect_to: str = Query(..., description="URL to redirect after successful authentication"),
    supabase: AsyncClient = Depends(get_supabase_client),
) -> dict[str, str]:
    """Initialize GitHub OAuth flow.

    Args:
        request: The incoming request
        redirect_to: URL to redirect after successful authentication
        supabase: Supabase client instance

    Returns:
        Dict containing the authorization URL
    """
    try:
        # Get the OAuth URL from Supabase
        auth_url = await supabase.auth.get_sign_in_with_oauth_url(
            "github",
            {
                "redirectTo": redirect_to,
                "scopes": "read:user user:email",
            },
        )
        return {"authorization_url": auth_url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize GitHub OAuth: {e!s}",
        )


@router.get("/callback")
@rate_limit("10/minute")
async def oauth_callback(
    request: Request,
    code: str = Query(..., description="OAuth authorization code"),
    state: str | None = Query(None, description="OAuth state parameter"),
    provider: str = Query(..., description="OAuth provider (google or github)"),
    supabase: AsyncClient = Depends(get_supabase_client),
    profile_service: ProfileService = Depends(ProfileService),
) -> dict[str, str]:
    """Handle OAuth callback.

    Args:
        request: The incoming request
        code: OAuth authorization code
        state: OAuth state parameter
        provider: OAuth provider name
        supabase: Supabase client instance
        profile_service: Profile service instance

    Returns:
        Dict containing the access token and user info
    """
    try:
        # Exchange code for token
        auth_response = await supabase.auth.exchange_code_for_session(code)

        if not auth_response or not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to authenticate with OAuth provider",
            )

        # Get or create user profile
        try:
            await profile_service.get_profile(auth_response.user.id)
        except HTTPException as e:
            if e.status_code == status.HTTP_404_NOT_FOUND:
                # Create profile if it doesn't exist
                await profile_service.create_profile(
                    auth_response.user.id,
                    {
                        "name": auth_response.user.user_metadata.get("name", ""),
                        "avatar_url": auth_response.user.user_metadata.get("avatar_url", ""),
                    },
                )

        return {
            "access_token": auth_response.session.access_token,
            "token_type": "bearer",
            "user": auth_response.user.model_dump(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process OAuth callback: {e!s}",
        )
