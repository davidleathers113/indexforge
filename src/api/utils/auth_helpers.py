"""Authentication helper utilities."""

import secrets

from fastapi import Cookie, Header, HTTPException, status
from supabase.client import AsyncClient

from src.api.config import Settings, get_settings
from src.api.middleware.csrf import generate_csrf_token, validate_csrf_token


async def validate_csrf(
    csrf_token: str | None = Cookie(None),
    x_csrf_token: str | None = Header(None),
) -> None:
    """Validate CSRF tokens if present."""
    if csrf_token and x_csrf_token:
        validate_csrf_token(csrf_token, x_csrf_token)


async def refresh_auth_tokens(supabase: AsyncClient) -> tuple[str, str]:
    """Refresh authentication tokens."""
    try:
        auth_response = await supabase.auth.refresh_session()
        if not auth_response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not refresh token",
            )
        return auth_response.session.access_token, generate_csrf_token()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed",
        ) from exc


def get_oauth_settings() -> tuple[Settings, str]:
    """Get OAuth settings and generate state token."""
    settings = get_settings()
    state = secrets.token_urlsafe(32)
    return settings, state
