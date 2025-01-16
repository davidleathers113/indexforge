"""Token-related authentication routes."""

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response, status
from supabase.client import AsyncClient

from src.api.dependencies.supabase import get_supabase_client
from src.api.models.responses import AuthResponse
from src.api.utils.auth_helpers import refresh_auth_tokens, validate_csrf
from src.api.utils.cookie_manager import set_auth_cookies


router = APIRouter(tags=["auth"])


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    response: Response,
    csrf_token: str = Cookie(...),
    x_csrf_token: str = Header(...),
    supabase: AsyncClient = Depends(get_supabase_client),
) -> AuthResponse:
    """Refresh the access token using the refresh token."""
    # Validate CSRF tokens
    await validate_csrf(csrf_token, x_csrf_token)

    try:
        # Refresh tokens
        access_token, new_csrf_token = await refresh_auth_tokens(supabase)

        # Create response
        auth_response = await supabase.auth.get_user()
        response_data = AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=auth_response.user.model_dump(),
        )

        # Set cookies
        set_auth_cookies(
            response=response,
            access_token=access_token,
            refresh_token=auth_response.session.refresh_token,
            csrf_token=new_csrf_token,
        )

        return response_data
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed",
        ) from exc
