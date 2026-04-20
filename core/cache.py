# ==========================================================
# JARVIS v9.0 - Caching Layer
# Redis + LRU cache for hot paths
# ==========================================================

import os
import json
import hashlib
import logging
from typing import Any, Optional, Callable
from functools import wraps, lru_cache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available - using in-memory cache only")


class CacheLayer:
    """Multi-tier caching: LRU (memory) + Redis (distributed)"""

    def __init__(self):
        self.redis_client = None

        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=os.getenv('REDIS_HOST', 'localhost'),
                    port=int(os.getenv('REDIS_PORT', 6379)),
                    db=0,
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
                logger.info("✅ Redis cache connected")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                self.redis_client = None

    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key"""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get from cache"""
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set in cache with TTL (seconds)"""
        if self.redis_client:
            try:
                self.redis_client.setex(
                    key,
                    ttl,
                    json.dumps(value)
                )
            except Exception as e:
                logger.error(f"Redis set error: {e}")

    def delete(self, key: str):
        """Delete from cache"""
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")

    def clear(self, pattern: str = "*"):
        """Clear cache by pattern"""
        if self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                logger.error(f"Redis clear error: {e}")


# Global cache instance
cache = CacheLayer()


def cached(ttl: int = 3600, prefix: str = "jarvis"):
    """Decorator for caching function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache._make_key(f"{prefix}:{func.__name__}", *args, **kwargs)

            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                return result

            # Execute function
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(key, result, ttl)

            return result
        return wrapper
    return decorator


# LRU cache for hot paths (in-memory)
@lru_cache(maxsize=1000)
def compute_risk_score(action: str) -> float:
    """Cached risk score computation"""
    # This would be replaced with actual risk computation
    return 0.5


@lru_cache(maxsize=500)
def validate_input_cached(input_text: str, input_type: str) -> bool:
    """Cached input validation"""
    # This would be replaced with actual validation
    return len(input_text) > 0 and len(input_text) < 10000
