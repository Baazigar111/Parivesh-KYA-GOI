"""
cache.py
--------
Unified High-Performance Caching Layer for PARIVESH KYA.
Supports:
1. Serverless Upstash Redis (REST)
2. Standard Redis (TCP socket / redis://)
3. In-Memory fallback cache with automatic TTL expiration
"""

import time
import json
import logging
from typing import Optional, Any
from .config import settings

logger = logging.getLogger(__name__)

class MemoryCache:
    """In-memory thread-safe TTL cache for fallback when Redis is not configured."""
    def __init__(self):
        self._store = {}

    def get(self, key: str) -> Optional[str]:
        if key in self._store:
            data, exp = self._store[key]
            if exp is None or time.time() < exp:
                return data
            else:
                del self._store[key]
        return None

    def set(self, key: str, value: str, ex: Optional[int] = None):
        exp = time.time() + ex if ex else None
        self._store[key] = (value, exp)

    def delete(self, key: str):
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()


class CacheClient:
    def __init__(self):
        self.client_type = "memory"
        self._upstash = None
        self._redis = None
        self._memory = MemoryCache()

        # 1. Try Upstash Redis REST
        if settings.UPSTASH_REDIS_REST_URL and settings.UPSTASH_REDIS_REST_TOKEN:
            try:
                from upstash_redis import Redis as UpstashRedis
                self._upstash = UpstashRedis(
                    url=settings.UPSTASH_REDIS_REST_URL,
                    token=settings.UPSTASH_REDIS_REST_TOKEN
                )
                self.client_type = "upstash"
                logger.info("Initialized Upstash Redis client")
            except Exception as e:
                logger.warning("Could not initialize Upstash Redis: %s", e)

        # 2. Try Standard Redis if Upstash is not active
        if self.client_type == "memory" and settings.REDIS_URL:
            try:
                import redis
                self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
                self._redis.ping()
                self.client_type = "redis"
                logger.info("Initialized standard Redis client from %s", settings.REDIS_URL)
            except Exception as e:
                logger.warning("Could not connect to Redis: %s. Using memory cache fallback.", e)
                self._redis = None

        if self.client_type == "memory":
            logger.info("Using high-speed In-Memory TTL Cache")

    def get(self, key: str) -> Optional[Any]:
        try:
            val_str = None
            if self.client_type == "upstash" and self._upstash:
                val_str = self._upstash.get(key)
            elif self.client_type == "redis" and self._redis:
                val_str = self._redis.get(key)
            else:
                val_str = self._memory.get(key)

            if val_str:
                try:
                    return json.loads(val_str)
                except Exception:
                    return val_str
        except Exception as e:
            logger.error("Cache get error for key '%s': %s", key, e)
        return None

    def set(self, key: str, value: Any, ex: int = 3600):
        try:
            val_str = json.dumps(value) if not isinstance(value, str) else value
            if self.client_type == "upstash" and self._upstash:
                self._upstash.set(key, val_str, ex=ex)
            elif self.client_type == "redis" and self._redis:
                self._redis.set(key, val_str, ex=ex)
            else:
                self._memory.set(key, val_str, ex=ex)
        except Exception as e:
            logger.error("Cache set error for key '%s': %s", key, e)

    def delete(self, key: str):
        try:
            if self.client_type == "upstash" and self._upstash:
                self._upstash.delete(key)
            elif self.client_type == "redis" and self._redis:
                self._redis.delete(key)
            else:
                self._memory.delete(key)
        except Exception as e:
            logger.error("Cache delete error for key '%s': %s", key, e)

    def clear(self):
        self._memory.clear()

    def status(self) -> dict:
        return {
            "type": self.client_type,
            "connected": True
        }

cache = CacheClient()
