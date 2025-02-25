import redis.asyncio as aioredis

from config.conf import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_CACHE_DB, CELERY_BROKER_DB

# Redis 默认提供 16 个数据库（编号从 0 到 15）
normal_cache_pool = aioredis.ConnectionPool(
    host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_CACHE_DB, decode_responses=True)
r_cache = aioredis.StrictRedis(connection_pool=normal_cache_pool)

celery_broker_pool = aioredis.ConnectionPool(
    host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=CELERY_BROKER_DB, decode_responses=True)
celery_broker = aioredis.StrictRedis(connection_pool=celery_broker_pool)


def init():
    if not r_cache.ping():
        raise Exception("Redis is not connected")

