from conf.config import settings


def get_cache_key(model: str, user_id: int) -> str:
    return f'{settings.REDIS_BATTLESHIP_CACHE_PREFIX}:{model}:{user_id}'
