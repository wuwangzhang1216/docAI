"""
Observability middleware for XinShouCai.

Provides:
- Request/response metrics collection
- Request ID tracking
- Structured request logging
- Error tracking
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.utils.logging_config import (
    clear_request_context,
    get_logger,
    set_request_context,
)
from app.utils.monitoring import (
    record_error,
    record_request,
    track_request_latency,
)

logger = get_logger("middleware.observability")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting observability data.

    Collects:
    - Request/response metrics (latency, status codes)
    - Request ID tracking
    - User context for logging
    """

    # Endpoints to skip for metrics (health checks, static files)
    SKIP_PATHS = {"/health", "/health/live", "/health/ready", "/metrics", "/favicon.ico"}

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics for certain paths
        path = request.url.path
        if path in self.SKIP_PATHS:
            return await call_next(request)

        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Set request context for logging
        set_request_context(request_id=request_id)

        # Get client info
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "unknown")

        # Normalize endpoint for metrics (remove path parameters)
        endpoint = self._normalize_path(path)
        method = request.method

        start_time = time.perf_counter()

        try:
            # Process request
            response = await call_next(request)

            # Calculate latency
            duration = time.perf_counter() - start_time
            duration_ms = duration * 1000

            # Record metrics
            record_request(method, endpoint, response.status_code)

            # Add response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

            # Log request
            self._log_request(
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                client_ip=client_ip,
                user_agent=user_agent,
            )

            # Track errors
            if response.status_code >= 400:
                error_type = self._get_error_type(response.status_code)
                record_error(error_type, endpoint)

            return response

        except Exception as e:
            # Calculate latency even on error
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Record error metrics
            record_request(method, endpoint, 500)
            record_error("internal", endpoint)

            # Log error
            logger.error(
                f"Request failed: {method} {path}",
                extra_data={
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e),
                    "client_ip": client_ip,
                },
                exc_info=True,
            )

            raise

        finally:
            clear_request_context()

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, handling proxies."""
        # Check X-Forwarded-For header (for load balancers/proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"

    def _normalize_path(self, path: str) -> str:
        """
        Normalize path for metrics by replacing dynamic segments.

        Examples:
            /api/v1/patients/123 -> /api/v1/patients/{id}
            /api/v1/conversations/456/messages -> /api/v1/conversations/{id}/messages
        """
        parts = path.split("/")
        normalized_parts = []

        for part in parts:
            # Check if part looks like an ID (numeric or UUID)
            if part.isdigit():
                normalized_parts.append("{id}")
            elif self._is_uuid(part):
                normalized_parts.append("{uuid}")
            else:
                normalized_parts.append(part)

        return "/".join(normalized_parts)

    def _is_uuid(self, value: str) -> bool:
        """Check if value looks like a UUID."""
        if len(value) == 36 and value.count("-") == 4:
            try:
                uuid.UUID(value)
                return True
            except ValueError:
                pass
        return False

    def _get_error_type(self, status_code: int) -> str:
        """Categorize error type from status code."""
        if status_code == 400:
            return "validation"
        elif status_code == 401:
            return "auth"
        elif status_code == 403:
            return "permission"
        elif status_code == 404:
            return "not_found"
        elif status_code == 429:
            return "rate_limit"
        elif 400 <= status_code < 500:
            return "client"
        else:
            return "internal"

    def _log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        client_ip: str,
        user_agent: str,
    ) -> None:
        """Log request with appropriate level based on status code."""
        log_data = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": client_ip,
            "user_agent": user_agent[:100],  # Truncate long user agents
        }

        if status_code >= 500:
            logger.error(f"{method} {path} {status_code}", extra_data=log_data)
        elif status_code >= 400:
            logger.warning(f"{method} {path} {status_code}", extra_data=log_data)
        elif duration_ms > 1000:  # Log slow requests as warning
            logger.warning(f"Slow request: {method} {path} {status_code}", extra_data=log_data)
        else:
            logger.info(f"{method} {path} {status_code}", extra_data=log_data)


class RequestIDMiddleware:
    """
    Simple middleware to add request ID to all requests.

    Can be used as an alternative to ObservabilityMiddleware
    when full metrics are not needed.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Generate request ID
            request_id = str(uuid.uuid4())

            # Store in scope for access in request handlers
            scope["request_id"] = request_id

            # Wrap send to add header to response
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.append((b"x-request-id", request_id.encode()))
                    message["headers"] = headers
                await send(message)

            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)
