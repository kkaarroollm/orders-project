import asyncio
import logging

from redis.asyncio import Redis

from src.config import settings
from src.streams import start_streams


async def connect_redis(url: str) -> Redis:
    client: Redis = Redis.from_url(url, decode_responses=True)
    if not await client.ping():
        raise ConnectionError("Could not connect to Redis")
    return client


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    redis = await connect_redis(settings.redis_url)
    try:
        await start_streams(redis)
    finally:
        await redis.close()


if __name__ == "__main__":
    asyncio.run(main())
