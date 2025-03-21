import os

import redis.asyncio as aioredis


async def connect_redis() -> aioredis.Redis:
    """Establish a connection to Redis."""
    redis_client: aioredis.Redis = aioredis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

    try:
        await redis_client.ping()
    except Exception as e:
        raise ConnectionError(f"Redis ping error: {e}") from e

    return redis_client
