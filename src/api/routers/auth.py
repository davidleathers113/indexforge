"""Authentication router."""

import secrets
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer
from supabase.client import AsyncClient

from src.api.config import get_settings
from src.api.dependencies.supabase import get_supabase_client
from src.api.middleware.csrf import generate_csrf_token, validate_csrf_token
from src.api.models.requests import (
    OAuthProvider,
    OAuthRequest,
    PasswordResetRequest,
    SignInRequest,
    SignUpRequest,
)
from src.api.models.responses import AuthResponse, UserProfile

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    csrf_token: str = Cookie(...),
    x_csrf_token: str = Header(...),
    supabase: AsyncClient = Depends(get_supabase_client),
) -> AuthResponse:
    """Refresh the access token using the refresh token."""
    validate_csrf_token(csrf_token, x_csrf_token)
    try:
        auth_response = await supabase.auth.refresh_session()
        if not auth_response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not refresh token"
            )
        new_csrf_token = generate_csrf_token()
        response = AuthResponse(
            access_token=auth_response.session.access_token,
            token_type="bearer",
            user=auth_response.user.model_dump(),
        )
        response.set_cookie(
            "csrf_token", new_csrf_token, httponly=True, secure=True, samesite="strict"
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token refresh failed")


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignUpRequest,
    supabase: AsyncClient = Depends(get_supabase_client),
    csrf_token: Optional[str] = Cookie(None),
    x_csrf_token: Optional[str] = Header(None),
) -> AuthResponse:
    """Sign up a new user."""
    if csrf_token and x_csrf_token:
        validate_csrf_token(csrf_token, x_csrf_token)
    try:
        auth_response = await supabase.auth.sign_up(
            {
                "email": request.email,
                "password": request.password,
                "options": {"data": {"name": request.name}},
            }
        )
        new_csrf_token = generate_csrf_token()
        response = AuthResponse(
            access_token=auth_response.session.access_token,
            token_type="bearer",
            user=auth_response.user.model_dump(),
        )
        response.set_cookie(
            "csrf_token", new_csrf_token, httponly=True, secure=True, samesite="strict"
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/signin", response_model=AuthResponse)
async def signin(
    request: SignInRequest,
    supabase: AsyncClient = Depends(get_supabase_client),
) -> AuthResponse:
    """Sign in an existing user."""
    try:
        auth_response = await supabase.auth.sign_in_with_password(
            {
                "email": request.email,
                "password": request.password,
            }
        )
        return AuthResponse(
            access_token=auth_response.session.access_token,
            token_type="bearer",
            user=auth_response.user.model_dump(),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


@router.post("/signout", status_code=status.HTTP_200_OK)
async def signout(
    supabase: AsyncClient = Depends(get_supabase_client),
) -> dict:
    """Sign out the current user."""
    try:
        await supabase.auth.sign_out()
        return {"message": "Successfully signed out"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: PasswordResetRequest,
    supabase: AsyncClient = Depends(get_supabase_client),
) -> dict:
    """Request a password reset."""
    try:
        await supabase.auth.reset_password_email(request.email)
        return {"message": "Password reset email sent"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me", response_model=UserProfile)
async def get_current_user(
    supabase: AsyncClient = Depends(get_supabase_client),
) -> UserProfile:
    """Get the current user's profile."""
    try:
        user = await supabase.auth.get_user()
        return UserProfile(
            id=user.user.id,
            email=user.user.email,
            name=user.user.user_metadata.get("name"),
            created_at=user.user.created_at,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


@router.post("/oauth/signin", response_model=AuthResponse)
async def oauth_signin(
    request: OAuthRequest,
    supabase: AsyncClient = Depends(get_supabase_client),
) -> RedirectResponse:
    """Initiate OAuth sign in flow."""
    try:
        settings = get_settings()
        state = secrets.token_urlsafe(32)

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

        response = RedirectResponse(url=auth_url)
        response.set_cookie(
            "oauth_state",
            state,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=300,  # 5 minutes
        )
        if request.redirect_to:
            response.set_cookie(
                "oauth_redirect",
                str(request.redirect_to),
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=300,
            )
        return response
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth initialization failed: {str(exc)}",
        ) from exc


@router.get("/oauth/callback/{provider}")
async def oauth_callback(
    request: Request,
    provider: OAuthProvider,
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None),
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

        settings = get_settings()

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
        response.delete_cookie("oauth_state")
        response.delete_cookie("oauth_redirect")

        # Set auth cookies
        response.set_cookie(
            "access_token",
            auth_response.session.access_token,
            httponly=True,
            secure=True,
            samesite="lax",
        )
        response.set_cookie(
            "refresh_token",
            auth_response.session.refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
        )

        return response
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth callback failed: {str(exc)}",
        ) from exc
