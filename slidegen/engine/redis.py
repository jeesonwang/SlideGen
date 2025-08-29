import redis
import redis.asyncio as aioredis

from slidegen.config import settings

# Redis provides 16 databases by default (numbered from 0 to 15).
r_cache = aioredis.StrictRedis.from_url(settings.REDIS_CACHE_URL.encoded_string())

r_cache_sync = redis.StrictRedis.from_url(settings.REDIS_CACHE_URL.encoded_string())


def init() -> None:
    if not r_cache_sync.ping():
        raise Exception("Redis is not connected")
