"""CSRF protection middleware."""

import hmac
import secrets

from fastapi import Cookie, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware


def generate_csrf_token() -> str:
    """Generate a new CSRF token."""
    return secrets.token_urlsafe(32)


def validate_csrf_token(cookie_token: str, header_token: str) -> bool:
    """Validate that the CSRF token in the cookie matches the one in the header.

    Args:
        cookie_token: The CSRF token from the cookie
        header_token: The CSRF token from the X-CSRF-Token header

    Returns:
        bool: True if the tokens match, False otherwise
    """
    if not cookie_token or not header_token:
        return False
    return hmac.compare_digest(cookie_token, header_token)


class CSRFMiddleware(BaseHTTPMiddleware):
    """Middleware for CSRF protection."""

    def __init__(self, app):
        """Initialize the CSRF middleware."""
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request and add CSRF protection.

        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain

        Returns:
            Response: The response from the next middleware/handler
        """
        # Skip CSRF check for safe methods
        if request.method in ("GET", "HEAD", "OPTIONS"):
            response = await call_next(request)
            return response

        # Get CSRF tokens from cookie and header
        csrf_cookie = request.cookies.get("csrf_token")
        csrf_header = request.headers.get("X-CSRF-Token")

        # Validate CSRF tokens
        if not csrf_cookie or not csrf_header or not validate_csrf_token(csrf_cookie, csrf_header):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid CSRF token",
            )

        response = await call_next(request)
        return response


class CSRFBearer(HTTPBearer):
    """Bearer token authentication with CSRF protection."""

    def __init__(self, auto_error: bool = True):
        """Initialize the CSRF bearer authentication."""
        super().__init__(auto_error=auto_error)

    async def __call__(
        self,
        request: Request,
        csrf_token: str | None = Cookie(None, alias="csrf_token"),
    ) -> str | None:
        """Validate the CSRF token.

        Args:
            request: The incoming request
            csrf_token: The CSRF token from the cookie

        Returns:
            Optional[str]: The validated CSRF token

        Raises:
            HTTPException: If the CSRF token is invalid
        """
        if not csrf_token:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token missing",
                )
            return None

        header_token = request.headers.get("X-CSRF-Token")
        if not header_token or not validate_csrf_token(csrf_token, header_token):
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid CSRF token",
                )
            return None

        return csrf_token
