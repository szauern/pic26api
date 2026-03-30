from redis.asyncio import Redis, from_url
from app.config import settings

# Globális Redis példány - nem app.state-en keresztül
redis_client: Redis | None = None


async def init_redis():
    global redis_client
    redis_client = from_url(settings.redis_url, encoding="utf-8", decode_responses=True)


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.aclose()
        redis_client = None


def get_redis() -> Redis:
    return redis_client
