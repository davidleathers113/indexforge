"""User-related authentication routes."""


from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response, status
from supabase.client import AsyncClient

from src.api.dependencies.supabase import get_supabase_client
from src.api.middleware.csrf import generate_csrf_token
from src.api.models.requests import PasswordResetRequest, SignInRequest, SignUpRequest
from src.api.models.responses import AuthResponse, UserProfile
from src.api.utils.auth_helpers import validate_csrf
from src.api.utils.cookie_manager import clear_auth_cookies, set_auth_cookies


router = APIRouter(tags=["auth"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignUpRequest,
    response: Response,
    supabase: AsyncClient = Depends(get_supabase_client),
    csrf_token: str | None = Cookie(None),
    x_csrf_token: str | None = Header(None),
) -> AuthResponse:
    """Sign up a new user."""
    await validate_csrf(csrf_token, x_csrf_token)

    try:
        # Create user
        auth_response = await supabase.auth.sign_up(
            {
                "email": request.email,
                "password": request.password,
                "options": {"data": {"name": request.name}},
            }
        )

        # Generate new CSRF token
        new_csrf_token = generate_csrf_token()

        # Create response
        response_data = AuthResponse(
            access_token=auth_response.session.access_token,
            token_type="bearer",
            user=auth_response.user.model_dump(),
        )

        # Set cookies
        set_auth_cookies(
            response=response,
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
            csrf_token=new_csrf_token,
        )

        return response_data
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/signin", response_model=AuthResponse)
async def signin(
    request: SignInRequest,
    response: Response,
    supabase: AsyncClient = Depends(get_supabase_client),
) -> AuthResponse:
    """Sign in an existing user."""
    try:
        # Sign in user
        auth_response = await supabase.auth.sign_in_with_password(
            {
                "email": request.email,
                "password": request.password,
            }
        )

        # Generate new CSRF token
        new_csrf_token = generate_csrf_token()

        # Create response
        response_data = AuthResponse(
            access_token=auth_response.session.access_token,
            token_type="bearer",
            user=auth_response.user.model_dump(),
        )

        # Set cookies
        set_auth_cookies(
            response=response,
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
            csrf_token=new_csrf_token,
        )

        return response_data
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        ) from exc


@router.post("/signout", status_code=status.HTTP_200_OK)
async def signout(
    response: Response,
    supabase: AsyncClient = Depends(get_supabase_client),
) -> dict:
    """Sign out the current user."""
    try:
        await supabase.auth.sign_out()
        clear_auth_cookies(response)
        return {"message": "Successfully signed out"}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: PasswordResetRequest,
    supabase: AsyncClient = Depends(get_supabase_client),
) -> dict:
    """Request a password reset."""
    try:
        await supabase.auth.reset_password_email(request.email)
        return {"message": "Password reset email sent"}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


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
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        ) from exc
