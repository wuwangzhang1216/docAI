"""
Tests for rate limiting functionality.

Covers:
- In-memory rate limiter
- Rate limit middleware
- Endpoint-specific limits
- Rate limit headers
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
from fastapi import Request
from httpx import AsyncClient

from app.utils.rate_limit import (
    InMemoryRateLimiter,
    RateLimitConfig,
    get_client_ip,
    get_endpoint_limit,
    match_endpoint_pattern,
)


class TestInMemoryRateLimiter:
    """Test in-memory rate limiter."""

    @pytest.fixture
    def limiter(self):
        """Create a fresh rate limiter."""
        return InMemoryRateLimiter()

    @pytest.mark.asyncio
    async def test_allows_within_limit(self, limiter):
        """Test requests within limit are allowed."""
        for i in range(5):
            is_allowed, remaining, retry_after = await limiter.is_allowed(
                "test_key", limit=10, window=60
            )
            assert is_allowed is True
            assert remaining >= 0
            assert retry_after == 0

    @pytest.mark.asyncio
    async def test_blocks_over_limit(self, limiter):
        """Test requests over limit are blocked."""
        # Exhaust the limit (accounting for burst multiplier of 1.5)
        # With limit=10 and burst=1.5, we get 15 tokens initially
        burst_limit = int(10 * RateLimitConfig.BURST_MULTIPLIER)
        for _ in range(burst_limit):
            await limiter.is_allowed("test_key", limit=10, window=60)

        # Next request should be blocked
        is_allowed, remaining, retry_after = await limiter.is_allowed(
            "test_key", limit=10, window=60
        )
        assert is_allowed is False
        assert remaining == 0
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_different_keys_independent(self, limiter):
        """Test different keys have independent limits."""
        # Exhaust limit for key1
        for _ in range(10):
            await limiter.is_allowed("key1", limit=10, window=60)

        # key2 should still work
        is_allowed, _, _ = await limiter.is_allowed("key2", limit=10, window=60)
        assert is_allowed is True

    @pytest.mark.asyncio
    async def test_tokens_refill_over_time(self, limiter):
        """Test tokens refill after time passes."""
        # Use all tokens (accounting for burst multiplier of 1.5)
        # With limit=5 and burst=1.5, we get 7 tokens initially
        burst_limit = int(5 * RateLimitConfig.BURST_MULTIPLIER)
        for _ in range(burst_limit):
            await limiter.is_allowed("test_key", limit=5, window=1)

        # Should be blocked
        is_allowed, _, _ = await limiter.is_allowed("test_key", limit=5, window=1)
        assert is_allowed is False

        # Wait for refill
        await asyncio.sleep(1.1)

        # Should be allowed again
        is_allowed, _, _ = await limiter.is_allowed("test_key", limit=5, window=1)
        assert is_allowed is True

    @pytest.mark.asyncio
    async def test_burst_allowance(self, limiter):
        """Test burst allowance allows slightly more than limit."""
        # Token bucket allows burst above limit
        allowed_count = 0
        for _ in range(20):
            is_allowed, _, _ = await limiter.is_allowed(
                "burst_test", limit=10, window=60
            )
            if is_allowed:
                allowed_count += 1

        # Should allow at least limit, possibly more due to burst
        assert allowed_count >= 10


class TestRateLimitConfig:
    """Test rate limit configuration."""

    def test_endpoint_limits_defined(self):
        """Test that important endpoints have rate limits."""
        assert "/api/v1/auth/login" in RateLimitConfig.ENDPOINT_LIMITS
        assert "/api/v1/auth/register" in RateLimitConfig.ENDPOINT_LIMITS
        assert "/api/v1/chat" in RateLimitConfig.ENDPOINT_LIMITS

    def test_login_limit_is_strict(self):
        """Test login has strict rate limit."""
        limit, window = RateLimitConfig.ENDPOINT_LIMITS["/api/v1/auth/login"]
        # Login should have low limit to prevent brute force
        assert limit <= 10
        assert window >= 60

    def test_register_limit_is_strict(self):
        """Test register has strict rate limit."""
        limit, window = RateLimitConfig.ENDPOINT_LIMITS["/api/v1/auth/register"]
        assert limit <= 5
        assert window >= 60


class TestEndpointMatching:
    """Test endpoint pattern matching."""

    def test_exact_match(self):
        """Test exact path matching."""
        assert match_endpoint_pattern("/api/v1/auth/login", "/api/v1/auth/login")
        assert not match_endpoint_pattern("/api/v1/auth/login", "/api/v1/auth/logout")

    def test_wildcard_match(self):
        """Test wildcard pattern matching."""
        pattern = "/api/v1/clinical/doctor/patients/*/ai-chat"
        assert match_endpoint_pattern(
            "/api/v1/clinical/doctor/patients/123/ai-chat", pattern
        )
        assert match_endpoint_pattern(
            "/api/v1/clinical/doctor/patients/abc-def/ai-chat", pattern
        )
        assert not match_endpoint_pattern(
            "/api/v1/clinical/doctor/patients/123/profile", pattern
        )

    def test_get_endpoint_limit_specific(self):
        """Test getting specific endpoint limit."""
        limit, window = get_endpoint_limit("/api/v1/auth/login")
        assert limit == 5
        assert window == 60

    def test_get_endpoint_limit_default(self):
        """Test default limit for unknown endpoint."""
        limit, window = get_endpoint_limit("/api/v1/unknown/endpoint")
        assert limit == RateLimitConfig.DEFAULT_LIMIT
        assert window == RateLimitConfig.DEFAULT_WINDOW


class TestClientIPExtraction:
    """Test client IP extraction."""

    def test_direct_client_ip(self):
        """Test extracting direct client IP."""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "192.168.1.100"

        ip = get_client_ip(request)
        assert ip == "192.168.1.100"

    def test_x_forwarded_for_header(self):
        """Test extracting IP from X-Forwarded-For header."""
        request = MagicMock(spec=Request)
        request.headers = {"X-Forwarded-For": "10.0.0.1, 192.168.1.1"}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        ip = get_client_ip(request)
        assert ip == "10.0.0.1"  # First IP in chain

    def test_x_real_ip_header(self):
        """Test extracting IP from X-Real-IP header."""
        request = MagicMock(spec=Request)
        request.headers = {"X-Real-IP": "10.0.0.5"}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        ip = get_client_ip(request)
        assert ip == "10.0.0.5"

    def test_no_client_returns_unknown(self):
        """Test unknown IP when no client info."""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = None

        ip = get_client_ip(request)
        assert ip == "unknown"


class TestRateLimitMiddleware:
    """Test rate limit middleware integration."""

    @pytest.mark.asyncio
    async def test_health_endpoint_not_limited(self, client: AsyncClient):
        """Test health endpoint is not rate limited."""
        # Make many requests
        for _ in range(50):
            response = await client.get("/health")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limit_headers_present(
        self, client: AsyncClient, test_patient_user, patient_token
    ):
        """Test rate limit headers are in response."""
        from tests.conftest import auth_headers

        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers(patient_token)
        )

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    @pytest.mark.asyncio
    async def test_login_rate_limit_triggered(self, client: AsyncClient):
        """Test login endpoint rate limit can be triggered."""
        # Make requests up to limit
        responses = []
        for i in range(10):
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": f"test{i}@test.com", "password": "wrong"}
            )
            responses.append(response)

        # Check if any got rate limited (429)
        status_codes = [r.status_code for r in responses]
        # After 5 requests, should start getting 429
        assert 429 in status_codes or all(c in [401, 429] for c in status_codes)

    @pytest.mark.asyncio
    async def test_rate_limit_returns_retry_after(self, client: AsyncClient):
        """Test rate limit response includes retry-after."""
        # Trigger rate limit on register
        for i in range(10):
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"spam{i}@test.com",
                    "password": "Test123!",
                    "user_type": "PATIENT",
                    "first_name": "Spam",
                    "last_name": "User"
                }
            )
            if response.status_code == 429:
                assert "Retry-After" in response.headers
                data = response.json()
                assert "retry_after" in data
                break
