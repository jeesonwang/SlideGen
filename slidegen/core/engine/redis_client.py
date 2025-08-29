import redis.asyncio as aioredis

from slidegen.core import settings

# Redis 默认提供 16 个数据库（编号从 0 到 15）
normal_cache_pool = aioredis.ConnectionPool.from_url(str(settings.REDIS_CACHE_URL), decode_responses=True)
r_cache = aioredis.StrictRedis(connection_pool=normal_cache_pool)

celery_broker_pool = aioredis.ConnectionPool.from_url(str(settings.CELERY_REDIS_URL), decode_responses=True)
celery_broker = aioredis.StrictRedis(connection_pool=celery_broker_pool)


def init() -> None:
    if not r_cache.ping():
        raise Exception("Redis is not connected")
