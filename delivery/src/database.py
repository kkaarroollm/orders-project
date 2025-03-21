import logging
import os

import redis.asyncio as aioredis
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


async def connect_mongo(mongo_url: str) -> tuple[AsyncIOMotorClient, AsyncIOMotorDatabase]:
    """Establish a connection to MongoDB."""
    mongo_client: AsyncIOMotorClient = AsyncIOMotorClient(mongo_url)
    db = mongo_client[os.getenv("MONGO_INITDB_DATABASE", "default")]

    try:
        await db.command("ping")
        logging.info("MongoDB connection established.")
    except Exception as e:
        raise ConnectionError(f"MongoDB ping error: {e}") from e

    return mongo_client, db


async def connect_redis() -> aioredis.Redis:
    """Establish a connection to Redis."""
    redis_client: aioredis.Redis = aioredis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

    try:
        await redis_client.ping()
        logging.info("Redis connection established.")
    except Exception as e:
        raise ConnectionError(f"Redis ping error: {e}") from e

    return redis_client
