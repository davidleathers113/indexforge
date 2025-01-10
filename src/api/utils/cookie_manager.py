"""Cookie management utilities."""

from typing import Optional

from fastapi import Response
from pydantic import HttpUrl


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: Optional[str] = None,
) -> None:
    """Set authentication cookies on the response."""
    # Set access token cookie
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600,  # 1 hour
    )

    # Set refresh token cookie
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 3600,  # 7 days
    )

    # Set CSRF token cookie if provided
    if csrf_token:
        response.set_cookie(
            "csrf_token",
            csrf_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=3600,  # 1 hour
        )


def set_oauth_cookies(
    response: Response,
    state: str,
    redirect_to: Optional[HttpUrl] = None,
) -> None:
    """Set OAuth-related cookies on the response."""
    # Set OAuth state cookie
    response.set_cookie(
        "oauth_state",
        state,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=300,  # 5 minutes
    )

    # Set redirect URL cookie if provided
    if redirect_to:
        response.set_cookie(
            "oauth_redirect",
            str(redirect_to),
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=300,  # 5 minutes
        )


def clear_auth_cookies(response: Response) -> None:
    """Clear all authentication-related cookies."""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    response.delete_cookie("csrf_token")


def clear_oauth_cookies(response: Response) -> None:
    """Clear all OAuth-related cookies."""
    response.delete_cookie("oauth_state")
    response.delete_cookie("oauth_redirect")
