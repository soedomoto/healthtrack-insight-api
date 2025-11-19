"""Redis caching layer for HealthTrack API.

Provides caching strategies for handling ~10K requests per minute scale:
- Health insights recommendations (1 hour cache)
- Metrics aggregations (5 minute cache)
- User profile cache (24 hour cache)
"""

import json
import logging
from typing import Optional, Any
from datetime import timedelta

import redis.asyncio as aioredis
from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class RedisCache:
    """Redis caching client for HealthTrack."""

    _instance: Optional["RedisCache"] = None

    def __init__(self):
        """Initialize Redis cache."""
        self.redis: Optional[aioredis.Redis] = None
        self.enabled = settings.ENABLE_REDIS_CACHE

    async def connect(self):
        """Connect to Redis."""
        if not self.enabled:
            logger.info("Redis caching disabled")
            return

        try:
            self.redis = await aioredis.from_url(settings.REDIS_URL, encoding="utf8")
            logger.info("Connected to Redis for caching")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.enabled = False

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.enabled or not self.redis:
            return None

        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"Cache GET error for key {key}: {e}")
        return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: int = 3600,
    ) -> bool:
        """Set value in cache with expiration."""
        if not self.enabled or not self.redis:
            return False

        try:
            await self.redis.set(key, json.dumps(value), ex=expire)
            return True
        except Exception as e:
            logger.warning(f"Cache SET error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self.enabled or not self.redis:
            return False

        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache DELETE error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self.enabled or not self.redis:
            return 0

        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache DELETE PATTERN error: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.enabled or not self.redis:
            return False

        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.warning(f"Cache EXISTS error for key {key}: {e}")
            return False


# Cache key generators
def get_recommendations_cache_key(user_id: int, days: int = 30) -> str:
    """Generate cache key for user recommendations."""
    return f"recommendations:user:{user_id}:days:{days}"


def get_metrics_summary_cache_key(user_id: int, days: int = 30) -> str:
    """Generate cache key for metrics summary."""
    return f"metrics_summary:user:{user_id}:days:{days}"


def get_user_cache_key(user_id: int) -> str:
    """Generate cache key for user profile."""
    return f"user:profile:{user_id}"


def get_user_goals_cache_key(user_id: int) -> str:
    """Generate cache key for user goals."""
    return f"user:goals:{user_id}"


# Global cache instance
_cache: Optional[RedisCache] = None


async def get_cache() -> RedisCache:
    """Get or create Redis cache instance."""
    global _cache
    if _cache is None:
        _cache = RedisCache()
        await _cache.connect()
    return _cache


async def invalidate_user_cache(user_id: int):
    """Invalidate all cache entries for a user."""
    cache = await get_cache()
    patterns = [
        f"recommendations:user:{user_id}:*",
        f"metrics_summary:user:{user_id}:*",
        f"user:profile:{user_id}",
        f"user:goals:{user_id}",
    ]

    for pattern in patterns:
        await cache.delete_pattern(pattern)

    logger.info(f"Invalidated cache for user {user_id}")


# ==================== CACHING STRATEGIES ====================
"""
Caching Strategy for ~10K requests/minute scale:

1. **Insights & Recommendations Cache** (1 hour TTL)
   - Generated recommendations cached per user
   - Invalidated on: new health metrics, goal updates
   - Hit rate target: 80-90%
   - Expected savings: 90% reduction in recommendations engine calls

2. **Metrics Aggregation Cache** (5 minute TTL)
   - Pre-aggregated metric statistics
   - Regenerated every 5 minutes
   - Hit rate target: 70-80%
   - Expected savings: 80% reduction in database aggregation queries

3. **User Profile Cache** (24 hour TTL)
   - User personal info (age, goals, preferences)
   - Updated on user profile changes
   - Hit rate target: 95%+
   - Expected savings: 95%+ reduction in user profile queries

Performance Implications:
- Reduces database load by ~80% during peak usage
- Enables handling 10K+ requests/minute with modest resources
- Trade-off: eventual consistency (max 1 hour stale data for recommendations)

Invalidation Strategy:
- Automatic: TTL expiration
- Manual: On data mutations (POST/PUT/DELETE operations)
- Pattern-based: Delete all cache keys for affected user
"""
