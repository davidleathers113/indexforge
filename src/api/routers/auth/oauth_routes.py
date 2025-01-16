"""OAuth-related authentication routes."""

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from supabase.client import AsyncClient

from src.api.dependencies.supabase import get_supabase_client
from src.api.models.requests import OAuthProvider, OAuthRequest
from src.api.utils.auth_helpers import get_oauth_settings
from src.api.utils.cookie_manager import clear_oauth_cookies, set_auth_cookies, set_oauth_cookies


router = APIRouter(tags=["auth"])


@router.post("/oauth/signin")
async def oauth_signin(
    request: OAuthRequest,
    response: Response,
    supabase: AsyncClient = Depends(get_supabase_client),
) -> RedirectResponse:
    """Initiate OAuth sign in flow."""
    try:
        settings, state = get_oauth_settings()

        # Generate provider-specific OAuth URL
        if request.provider == OAuthProvider.GOOGLE:
            params = {
                "client_id": settings.google_client_id,
                "redirect_uri": f"{settings.oauth_redirect_url}/google",
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "access_type": "offline",
            }
            auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        elif request.provider == OAuthProvider.GITHUB:
            params = {
                "client_id": settings.github_client_id,
                "redirect_uri": f"{settings.oauth_redirect_url}/github",
                "scope": "user:email",
                "state": state,
            }
            auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {request.provider}",
            )

        # Create redirect response
        response = RedirectResponse(url=auth_url)

        # Set OAuth cookies
        set_oauth_cookies(
            response=response,
            state=state,
            redirect_to=request.redirect_to,
        )

        return response
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth initialization failed: {exc!s}",
        ) from exc


@router.get("/oauth/callback/{provider}")
async def oauth_callback(
    request: Request,
    provider: OAuthProvider,
    code: str = Query(...),
    state: str = Query(...),
    error: str | None = Query(None),
    supabase: AsyncClient = Depends(get_supabase_client),
) -> RedirectResponse:
    """Handle OAuth callback."""
    try:
        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth error: {error}",
            )

        # Verify state parameter
        stored_state = request.cookies.get("oauth_state")
        if not stored_state or stored_state != state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter",
            )

        settings = get_oauth_settings()[0]

        # Exchange code for tokens based on provider
        if provider == OAuthProvider.GOOGLE:
            auth_response = await supabase.auth.sign_in_with_oauth(
                {
                    "provider": "google",
                    "code": code,
                    "options": {
                        "redirect_to": settings.oauth_redirect_url,
                    },
                }
            )
        elif provider == OAuthProvider.GITHUB:
            auth_response = await supabase.auth.sign_in_with_oauth(
                {
                    "provider": "github",
                    "code": code,
                    "options": {
                        "redirect_to": settings.oauth_redirect_url,
                    },
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider}",
            )

        # Get redirect URL from cookie or use default
        redirect_to = request.cookies.get("oauth_redirect", "/dashboard")
        response = RedirectResponse(url=redirect_to)

        # Clear OAuth cookies
        clear_oauth_cookies(response)

        # Set auth cookies
        set_auth_cookies(
            response=response,
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
        )

        return response
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth callback failed: {exc!s}",
        ) from exc
