import logging

import redis.asyncio as aioredis


async def connect_redis(url: str) -> aioredis.Redis:
    redis_client: aioredis.Redis = aioredis.from_url(url, decode_responses=True)  # type: ignore[assignment]

    try:
        await redis_client.ping()
        logging.info("Redis connection established.")
    except Exception as e:
        raise ConnectionError(f"Redis ping error: {e}") from e

    return redis_client
