"""
Rate limiting middleware and utilities.

Provides:
- Token bucket algorithm implementation
- Redis-based distributed rate limiting
- In-memory fallback for development
- Configurable limits per endpoint
- IP-based and user-based rate limiting

Design Goals:
1. Protect sensitive endpoints (login, register, chat)
2. Prevent abuse and DoS attacks
3. Fair usage for all users
4. Graceful degradation when Redis unavailable
"""

import time
import asyncio
from typing import Optional, Callable, Dict, Tuple
from functools import wraps
from collections import defaultdict

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis

from app.config import settings


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": retry_after
            },
            headers={"Retry-After": str(retry_after)}
        )


class RateLimitConfig:
    """Configuration for rate limiting."""

    # Default limits (requests per window)
    DEFAULT_LIMIT = 100
    DEFAULT_WINDOW = 60  # seconds

    # Endpoint-specific limits
    ENDPOINT_LIMITS: Dict[str, Tuple[int, int]] = {
        # Auth endpoints - strict limits to prevent brute force
        "/api/v1/auth/login": (5, 60),           # 5 requests per minute
        "/api/v1/auth/register": (3, 60),        # 3 requests per minute
        "/api/v1/auth/change-password": (3, 60), # 3 requests per minute

        # Chat endpoints - moderate limits
        "/api/v1/chat": (30, 60),                # 30 messages per minute
        "/api/v1/chat/pre-visit": (30, 60),      # 30 messages per minute

        # Clinical endpoints
        "/api/v1/clinical/checkin": (10, 60),    # 10 per minute
        "/api/v1/clinical/assessment": (10, 60), # 10 per minute

        # Doctor AI chat - moderate limits
        "/api/v1/clinical/doctor/patients/*/ai-chat": (20, 60),  # 20 per minute
    }

    # Global rate limit (per IP)
    GLOBAL_LIMIT = 200  # requests per minute
    GLOBAL_WINDOW = 60

    # Burst allowance - allows short bursts above limit
    BURST_MULTIPLIER = 1.5


class InMemoryRateLimiter:
    """
    In-memory rate limiter using token bucket algorithm.

    Used as fallback when Redis is unavailable.
    Note: Does not work across multiple instances.
    """

    def __init__(self):
        self._buckets: Dict[str, Dict] = defaultdict(
            lambda: {"tokens": 0, "last_update": 0}
        )
        self._lock = asyncio.Lock()

    async def is_allowed(
        self,
        key: str,
        limit: int,
        window: int
    ) -> Tuple[bool, int, int]:
        """
        Check if request is allowed under rate limit.

        Args:
            key: Unique identifier (e.g., "ip:192.168.1.1" or "user:123")
            limit: Maximum requests allowed in window
            window: Time window in seconds

        Returns:
            Tuple of (is_allowed, remaining_requests, retry_after_seconds)
        """
        async with self._lock:
            now = time.time()
            bucket = self._buckets[key]

            # Calculate token refill rate (tokens per second)
            refill_rate = limit / window

            # Time since last update
            time_passed = now - bucket["last_update"]

            # Refill tokens
            bucket["tokens"] = min(
                limit * RateLimitConfig.BURST_MULTIPLIER,
                bucket["tokens"] + (time_passed * refill_rate)
            )
            bucket["last_update"] = now

            if bucket["tokens"] >= 1:
                bucket["tokens"] -= 1
                remaining = int(bucket["tokens"])
                return True, remaining, 0
            else:
                # Calculate retry after
                tokens_needed = 1 - bucket["tokens"]
                retry_after = int(tokens_needed / refill_rate) + 1
                return False, 0, retry_after


class RedisRateLimiter:
    """
    Redis-based distributed rate limiter using sliding window algorithm.

    Supports multiple application instances.
    """

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None
        self._connected = False

    async def connect(self):
        """Connect to Redis."""
        if not self._connected:
            try:
                self._client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self._client.ping()
                self._connected = True
            except Exception as e:
                print(f"Redis connection failed: {e}")
                self._connected = False

    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._connected = False

    async def is_allowed(
        self,
        key: str,
        limit: int,
        window: int
    ) -> Tuple[bool, int, int]:
        """
        Check if request is allowed using sliding window counter.

        Uses Redis sorted sets for efficient sliding window implementation.

        Args:
            key: Unique identifier
            limit: Maximum requests in window
            window: Time window in seconds

        Returns:
            Tuple of (is_allowed, remaining_requests, retry_after_seconds)
        """
        if not self._connected:
            await self.connect()

        if not self._connected or not self._client:
            # Fallback: allow request if Redis unavailable
            return True, limit, 0

        try:
            now = time.time()
            window_start = now - window

            # Use pipeline for atomic operations
            pipe = self._client.pipeline()

            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)

            # Count current requests in window
            pipe.zcard(key)

            # Add current request with timestamp as score
            pipe.zadd(key, {f"{now}:{id(now)}": now})

            # Set expiry on the key
            pipe.expire(key, window + 1)

            results = await pipe.execute()
            current_count = results[1]

            if current_count < limit:
                remaining = limit - current_count - 1
                return True, max(0, remaining), 0
            else:
                # Get oldest entry to calculate retry time
                oldest = await self._client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_time = oldest[0][1]
                    retry_after = int(oldest_time + window - now) + 1
                else:
                    retry_after = window
                return False, 0, max(1, retry_after)

        except Exception as e:
            print(f"Redis rate limit error: {e}")
            # Fallback: allow on error
            return True, limit, 0


# Global rate limiter instances
_redis_limiter: Optional[RedisRateLimiter] = None
_memory_limiter: Optional[InMemoryRateLimiter] = None


def get_rate_limiter() -> InMemoryRateLimiter | RedisRateLimiter:
    """Get the appropriate rate limiter instance."""
    global _redis_limiter, _memory_limiter

    if settings.REDIS_URL and settings.REDIS_URL != "redis://localhost:6379/0":
        if _redis_limiter is None:
            _redis_limiter = RedisRateLimiter(settings.REDIS_URL)
        return _redis_limiter
    else:
        if _memory_limiter is None:
            _memory_limiter = InMemoryRateLimiter()
        return _memory_limiter


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    # Check X-Forwarded-For header (for reverse proxies)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Get the first IP (original client)
        return forwarded.split(",")[0].strip()

    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to direct client IP
    if request.client:
        return request.client.host

    return "unknown"


def get_user_id(request: Request) -> Optional[str]:
    """Extract user ID from request if authenticated."""
    # Try to get user from request state (set by auth middleware)
    user = getattr(request.state, "user", None)
    if user:
        return str(user.id)
    return None


def match_endpoint_pattern(path: str, pattern: str) -> bool:
    """Match path against pattern with wildcard support."""
    if "*" not in pattern:
        return path == pattern

    # Simple wildcard matching
    parts = pattern.split("*")
    if len(parts) == 2:
        return path.startswith(parts[0]) and path.endswith(parts[1])

    return False


def get_endpoint_limit(path: str) -> Tuple[int, int]:
    """Get rate limit for specific endpoint."""
    for pattern, (limit, window) in RateLimitConfig.ENDPOINT_LIMITS.items():
        if match_endpoint_pattern(path, pattern):
            return limit, window
    return RateLimitConfig.DEFAULT_LIMIT, RateLimitConfig.DEFAULT_WINDOW


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.

    Applies both global (IP-based) and endpoint-specific limits.
    """

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        limiter = get_rate_limiter()
        client_ip = get_client_ip(request)
        path = request.url.path

        # 1. Check global rate limit (per IP)
        global_key = f"ratelimit:global:{client_ip}"
        is_allowed, remaining, retry_after = await limiter.is_allowed(
            global_key,
            RateLimitConfig.GLOBAL_LIMIT,
            RateLimitConfig.GLOBAL_WINDOW
        )

        if not is_allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Global rate limit exceeded. Please slow down.",
                    "retry_after": retry_after
                },
                headers={"Retry-After": str(retry_after)}
            )

        # 2. Check endpoint-specific limit
        limit, window = get_endpoint_limit(path)
        endpoint_key = f"ratelimit:endpoint:{path}:{client_ip}"

        # For authenticated requests, also include user ID
        user_id = get_user_id(request)
        if user_id:
            endpoint_key = f"ratelimit:endpoint:{path}:user:{user_id}"

        is_allowed, remaining, retry_after = await limiter.is_allowed(
            endpoint_key, limit, window
        )

        if not is_allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded for this endpoint. Please try again later.",
                    "retry_after": retry_after
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after)
                }
            )

        # Proceed with request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window)

        return response


def rate_limit(
    limit: int = 10,
    window: int = 60,
    key_func: Optional[Callable[[Request], str]] = None
):
    """
    Decorator for applying rate limits to specific endpoints.

    Usage:
        @router.post("/endpoint")
        @rate_limit(limit=5, window=60)
        async def my_endpoint():
            ...

    Args:
        limit: Maximum requests allowed in window
        window: Time window in seconds
        key_func: Optional function to generate rate limit key from request
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            limiter = get_rate_limiter()
            client_ip = get_client_ip(request)

            if key_func:
                key = key_func(request)
            else:
                key = f"ratelimit:decorator:{func.__name__}:{client_ip}"

            is_allowed, remaining, retry_after = await limiter.is_allowed(
                key, limit, window
            )

            if not is_allowed:
                raise RateLimitExceeded(retry_after=retry_after)

            return await func(request, *args, **kwargs)

        return wrapper
    return decorator


# Cleanup function for shutdown
async def cleanup_rate_limiters():
    """Cleanup rate limiter connections."""
    global _redis_limiter
    if _redis_limiter:
        await _redis_limiter.close()
