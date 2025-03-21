import asyncio
import logging
import os

from redis.asyncio import Redis

from src.utils import start_stream_worker


async def connect_redis() -> Redis:
    client = Redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)
    if not await client.ping():
        raise ConnectionError("Could not connect to Redis")
    return client


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    redis_client = await connect_redis()
    try:
        await start_stream_worker(redis_client)
    finally:
        await redis_client.close()


if __name__ == "__main__":
    asyncio.run(main())
