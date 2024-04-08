from typing import Any

import orjson

from webapp.cache.key_builder import get_cache_key
from webapp.db.redis import get_redis
from webapp.metrics.metrics import INTEGRATIONS_LATENCY


@INTEGRATIONS_LATENCY.time()
async def redis_set(model: str, user_id: int, data: Any) -> None:
    redis = get_redis()
    key = get_cache_key(model, user_id)
    print(key)
    await redis.set(key, orjson.dumps(data))


@INTEGRATIONS_LATENCY.time()
async def redis_get(model: str, user_id: int) -> Any:
    redis = get_redis()
    key = get_cache_key(model, user_id)
    print(key)
    cached = await redis.get(key)

    if cached is None:
        return None

    return orjson.loads(cached)


@INTEGRATIONS_LATENCY.time()
async def redis_remove(model: str, user_id: int) -> None:
    redis = get_redis()
    key = get_cache_key(model, user_id)
    await redis.delete(key)
