from redis.asyncio import Redis


async def connect_redis(url: str) -> Redis:
    """Establish a connection to Redis."""
    redis_client: Redis = Redis.from_url(url, decode_responses=True)

    try:
        await redis_client.ping()
    except Exception as e:
        raise ConnectionError(f"Redis ping error: {e}") from e

    return redis_client
