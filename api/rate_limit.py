import asyncio
import logging
import os
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def allow(self, key: str) -> bool:
        now = time.time()
        async with self._lock:
            bucket = self._buckets[key]
            cutoff = now - self.window_seconds
            while bucket and bucket[0] < cutoff:
                bucket.popleft()

            if len(bucket) >= self.max_requests:
                return False

            bucket.append(now)
            return True


class RedisRateLimiter:
    """
    Distributed sliding-window rate limiter backed by Redis.
    Uses a sorted-set per key; falls back to allowing the request on Redis errors
    so a Redis outage does not block the API entirely.
    """

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._client: Optional[object] = None
        self._available = False
        self._init_redis()

    def _init_redis(self) -> None:
        try:
            import redis
            host = os.getenv("REDIS_HOST", "localhost")
            port = int(os.getenv("REDIS_PORT", "6379"))
            self._client = redis.Redis(host=host, port=port, decode_responses=True, socket_connect_timeout=1)
            self._client.ping()
            self._available = True
            logger.info("RedisRateLimiter: connected to Redis at %s:%s", host, port)
        except Exception as exc:
            logger.warning("RedisRateLimiter: Redis unavailable (%s), falling back to allow-all", exc)
            self._available = False

    async def allow(self, key: str) -> bool:
        if not self._available or self._client is None:
            return True  # graceful fallback: allow when Redis is down

        try:
            now = time.time()
            window_start = now - self.window_seconds
            redis_key = f"rl:{key}"

            pipe = self._client.pipeline()
            pipe.zremrangebyscore(redis_key, "-inf", window_start)
            pipe.zcard(redis_key)
            pipe.zadd(redis_key, {str(now): now})
            pipe.expire(redis_key, self.window_seconds + 1)
            results = await asyncio.to_thread(pipe.execute)

            count_before_add = results[1]
            return count_before_add < self.max_requests
        except Exception as exc:
            logger.warning("RedisRateLimiter: error during allow check (%s), permitting request", exc)
            return True  # fail-open on transient errors
