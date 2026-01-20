"""
JWT Token Blacklist Service

Provides token revocation functionality using Redis.
Tokens are stored in Redis with their JTI (JWT ID) as the key,
and expire automatically based on the token's expiration time.
"""

import logging
from datetime import datetime
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Redis client (initialized lazily)
_redis_client = None


async def get_redis_client():
    """Get or create Redis client."""
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    try:
        import redis.asyncio as redis

        _redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        # Test connection
        await _redis_client.ping()
        logger.info("Redis connection established for token blacklist")
        return _redis_client
    except Exception as e:
        logger.warning(f"Redis not available for token blacklist: {e}")
        return None


class TokenBlacklist:
    """
    Manages JWT token blacklist using Redis.

    Features:
    - Add tokens to blacklist with automatic expiration
    - Check if a token is blacklisted
    - Graceful fallback when Redis is unavailable
    """

    BLACKLIST_PREFIX = "token_blacklist:"

    @classmethod
    async def add_to_blacklist(
        cls,
        jti: str,
        expires_at: datetime,
        user_id: Optional[str] = None,
        reason: str = "logout",
    ) -> bool:
        """
        Add a token to the blacklist.

        Args:
            jti: The JWT ID (unique identifier for the token)
            expires_at: When the token expires (used for auto-cleanup)
            user_id: Optional user ID for logging
            reason: Reason for blacklisting (logout, revoked, etc.)

        Returns:
            True if successfully blacklisted, False otherwise
        """
        redis = await get_redis_client()

        if redis is None:
            logger.warning("Redis unavailable - token not blacklisted")
            return False

        try:
            # Calculate TTL based on token expiration
            # Add a small buffer (1 hour) to ensure token stays blacklisted
            ttl_seconds = int((expires_at - datetime.utcnow()).total_seconds())
            ttl_seconds = max(ttl_seconds, 60)  # Minimum 1 minute
            ttl_seconds = min(ttl_seconds, 86400 * 7)  # Maximum 7 days

            key = f"{cls.BLACKLIST_PREFIX}{jti}"
            value = f"{user_id or 'unknown'}:{reason}:{datetime.utcnow().isoformat()}"

            await redis.setex(key, ttl_seconds, value)
            logger.info(f"Token blacklisted: jti={jti[:8]}..., reason={reason}")
            return True

        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False

    @classmethod
    async def is_blacklisted(cls, jti: str) -> bool:
        """
        Check if a token is blacklisted.

        Args:
            jti: The JWT ID to check

        Returns:
            True if the token is blacklisted, False otherwise
        """
        redis = await get_redis_client()

        if redis is None:
            # If Redis is unavailable, assume token is valid
            # This is a security trade-off for availability
            return False

        try:
            key = f"{cls.BLACKLIST_PREFIX}{jti}"
            result = await redis.exists(key)
            return bool(result)

        except Exception as e:
            logger.error(f"Failed to check token blacklist: {e}")
            return False

    @classmethod
    async def revoke_all_user_tokens(cls, user_id: str) -> int:
        """
        Revoke all tokens for a specific user.

        Note: This requires storing active tokens, which adds complexity.
        For now, this is a placeholder that returns 0.

        A full implementation would require:
        1. Storing all active token JTIs per user
        2. Iterating and blacklisting each one

        Args:
            user_id: The user whose tokens should be revoked

        Returns:
            Number of tokens revoked
        """
        logger.info(f"Token revocation requested for user: {user_id}")
        # This would require tracking active tokens per user
        # For now, we rely on individual token logout
        return 0


async def cleanup_blacklist():
    """
    Clean up expired entries from the blacklist.

    Note: Redis automatically handles expiration via TTL,
    so this is only needed for manual cleanup scenarios.
    """
    redis = await get_redis_client()

    if redis is None:
        return

    # Redis handles TTL-based cleanup automatically
    # This function is here for potential future needs
    logger.info("Blacklist cleanup not needed - Redis handles TTL automatically")
