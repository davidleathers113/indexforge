"""Monitoring middleware.

This module provides middleware for monitoring HTTP requests and responses.
"""

import time
from typing import Callable

from prometheus_client import REGISTRY, generate_latest

from src.api.monitoring.prometheus_metrics import HTTP_REQUEST_DURATION, HTTP_REQUESTS_TOTAL


def timing_middleware() -> Callable:
    """Create middleware for timing HTTP requests.

    Returns:
        Middleware function for FastAPI
    """

    async def middleware(request, call_next):
        start_time = time.perf_counter()
        response = None

        try:
            response = await call_next(request)
        except Exception:
            # Record error metrics
            endpoint = request.url.path
            for param_name, param_value in request.path_params.items():
                endpoint = endpoint.replace(str(param_value), f"{{{param_name}}}")

            HTTP_REQUEST_DURATION.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=500,
            ).observe(time.perf_counter() - start_time)

            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=500,
            ).inc()
            raise
        finally:
            if response is not None:
                duration = time.perf_counter() - start_time

                # Extract endpoint pattern (replace path parameters with placeholders)
                endpoint = request.url.path
                for param_name, param_value in request.path_params.items():
                    endpoint = endpoint.replace(str(param_value), f"{{{param_name}}}")

                # Record metrics
                HTTP_REQUEST_DURATION.labels(
                    method=request.method,
                    endpoint=endpoint,
                    status_code=response.status_code,
                ).observe(duration)

                HTTP_REQUESTS_TOTAL.labels(
                    method=request.method,
                    endpoint=endpoint,
                    status_code=response.status_code,
                ).inc()

        return response

    return middleware


def get_metrics() -> str:
    """Generate OpenMetrics-compatible metrics output.

    Returns:
        Metrics in OpenMetrics format
    """
    return generate_latest(REGISTRY).decode("utf-8")
