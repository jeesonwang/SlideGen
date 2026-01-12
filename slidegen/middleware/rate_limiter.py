"""
Simple in-memory rate limiter for SSE endpoints

NOTE: For production use with multiple workers, consider using:
- slowapi (with Redis backend)
- fastapi-limiter (with Redis backend)

This implementation is suitable for single-process deployments.
"""

import time
from collections import defaultdict

from fastapi import HTTPException, Request


class SimpleRateLimiter:
    """Simple in-memory rate limiter using sliding window"""

    def __init__(self, times: int = 5, window: int = 60):
        """
        Initialize rate limiter

        Args:
            times: Maximum number of requests allowed
            window: Time window in seconds
        """
        self.times = times
        self.window = window
        # Format: {identifier: [timestamp1, timestamp2, ...]}
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _get_identifier(self, request: Request) -> str:
        """Get unique identifier for the request (user_id or IP)"""
        # Try to get user from request state (set by auth middleware)
        user = getattr(request.state, "user", None)
        if user and hasattr(user, "id"):
            return f"user:{user.id}"

        # Fall back to client IP
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"

    def _clean_old_requests(self, identifier: str, current_time: float) -> None:
        """Remove requests outside the time window"""
        cutoff_time = current_time - self.window
        self._requests[identifier] = [ts for ts in self._requests[identifier] if ts > cutoff_time]

    async def __call__(self, request: Request) -> None:
        """Check rate limit for the request"""
        identifier = self._get_identifier(request)
        current_time = time.time()

        # Clean old requests
        self._clean_old_requests(identifier, current_time)

        # Check if limit exceeded
        if len(self._requests[identifier]) >= self.times:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {self.times} requests per {self.window} seconds.",
            )

        # Record this request
        self._requests[identifier].append(current_time)


# Global rate limiter instances
sse_rate_limiter = SimpleRateLimiter(times=5, window=60)  # 5 requests per minute
