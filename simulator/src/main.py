import asyncio
import logging

from shared.redis.connection import connect_redis

from src.settings import settings
from src.streams import start_streams


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    redis = await connect_redis(settings.redis_url)
    try:
        await start_streams(redis)
    finally:
        await redis.close()


if __name__ == "__main__":
    asyncio.run(main())
