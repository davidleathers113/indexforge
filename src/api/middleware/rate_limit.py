"""Rate limiting middleware for API endpoints."""

from typing import Callable

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

limiter = Limiter(key_func=get_remote_address)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process the request and apply rate limiting.

        Args:
            request: The incoming request
            call_next: The next middleware or endpoint to call

        Returns:
            The response from the next middleware or endpoint
        """
        # Add rate limit headers to the response
        response = await call_next(request)
        if hasattr(request.state, "view_rate_limit"):
            response.headers["X-RateLimit-Limit"] = str(request.state.view_rate_limit.limit)
            response.headers["X-RateLimit-Remaining"] = str(request.state.view_rate_limit.remaining)
            response.headers["X-RateLimit-Reset"] = str(request.state.view_rate_limit.reset_at)
        return response


def rate_limit(
    limit: str = "100/minute",
    key_func: Callable = get_remote_address,
) -> Callable:
    """Decorator for rate limiting specific endpoints.

    Args:
        limit: Rate limit string (e.g., "100/minute", "1000/day")
        key_func: Function to generate the rate limit key

    Returns:
        Decorator function for rate limiting
    """
    return limiter.limit(limit, key_func=key_func)
