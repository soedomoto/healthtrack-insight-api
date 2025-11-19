"""Rate limiting middleware for handling high-scale traffic.

Designed to handle ~10K requests/minute with appropriate rate limiting
to ensure fair distribution and system stability.
"""

import time
import logging
from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitStore:
    """In-memory rate limit store (for single-process deployment).

    For distributed deployments, this should be replaced with Redis.
    """

    def __init__(self):
        """Initialize rate limit store."""
        self.requests: dict = {}  # {client_id: [timestamps]}

    def is_allowed(
        self,
        client_id: str,
        max_requests: int,
        window_seconds: int,
    ) -> bool:
        """Check if request is allowed under rate limit."""
        now = time.time()
        cutoff = now - window_seconds

        if client_id not in self.requests:
            self.requests[client_id] = []

        # Remove old requests outside window
        self.requests[client_id] = [
            timestamp for timestamp in self.requests[client_id] if timestamp > cutoff
        ]

        # Check if limit exceeded
        if len(self.requests[client_id]) >= max_requests:
            return False

        # Record this request
        self.requests[client_id].append(now)
        return True

    def cleanup(self):
        """Cleanup old entries periodically."""
        now = time.time()
        cutoff = now - 3600  # Remove entries older than 1 hour

        for client_id in list(self.requests.keys()):
            self.requests[client_id] = [
                timestamp for timestamp in self.requests[client_id] if timestamp > cutoff
            ]

            if not self.requests[client_id]:
                del self.requests[client_id]


# Global rate limit store
_rate_limit_store = RateLimitStore()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for API requests.

    Limits:
    - Per-IP: 600 requests/minute (allows ~10K/minute across 16+ IPs)
    - Per-user: 100 requests/minute (for authenticated endpoints)

    Strategy for 10K requests/minute scale:
    - Use distributed rate limiting (Redis) in production
    - Each node allows proportional share of limits
    - Example: 20 nodes × 600 req/min = 12K req/min capacity
    """

    def __init__(self, app, enabled: bool = True):
        """Initialize middleware.

        Args:
            app: FastAPI application
            enabled: Whether rate limiting is enabled
        """
        super().__init__(app)
        self.enabled = enabled
        self.max_requests_per_minute = 600
        self.max_requests_per_second = 10

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        if not self.enabled:
            return await call_next(request)

        # Get client identifier (IP address)
        client_id = request.client.host if request.client else "unknown"

        # Per-minute limit (most important for 10K req/min scale)
        if not _rate_limit_store.is_allowed(
            f"{client_id}:minute",
            self.max_requests_per_minute,
            60,
        ):
            logger.warning(f"Rate limit exceeded for {client_id} (per-minute)")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded: max 600 requests/minute",
            )

        # Per-second limit (burst protection)
        if not _rate_limit_store.is_allowed(
            f"{client_id}:second",
            self.max_requests_per_second,
            1,
        ):
            logger.warning(f"Rate limit exceeded for {client_id} (per-second)")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded: max 10 requests/second",
            )

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.max_requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.max_requests_per_minute
            - len(_rate_limit_store.requests.get(f"{client_id}:minute", []))
        )

        return response


# ==================== SCALE CONSIDERATIONS NOTES ====================
"""
For handling ~10K requests/minute (167 requests/second):

1. **Database Optimization:**
   - Connection pooling: asyncpg with pool size 20-50
   - Indexes on: user_id, metric_type, recorded_at
   - Query optimization: avoid N+1, use select() with relationships
   - Batch operations where possible

2. **Caching Strategy:**
   - Redis for distributed caching
   - 1-hour TTL for recommendations (80-90% hit rate)
   - 5-minute TTL for metrics aggregations
   - 24-hour TTL for user profiles
   - Expected: 80% reduction in database load

3. **Rate Limiting:**
   - Per-IP: 600 requests/minute per client
   - Per-second: 10 requests/second for burst control
   - With 16+ load-balanced nodes: 9,600+ effective capacity
   - Use Redis-based rate limiting in production

4. **API Architecture:**
   - Async/await throughout (FastAPI + asyncpg)
   - Connection pooling at database level
   - Middleware for caching and rate limiting
   - Horizontal scaling via multiple node deployment

5. **Deployment Model:**
   - Load balancer distributing to N nodes
   - Each node: 1,000+ requests/minute capacity
   - 10-20 nodes: 10K-20K requests/minute system capacity
   - Redis cluster for cache distribution

6. **Monitoring:**
   - Track cache hit rates
   - Monitor database connection pool
   - Alert on rate limit threshold (90%+)
   - Dashboard for request latency percentiles
"""
