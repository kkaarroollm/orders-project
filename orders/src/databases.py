from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from redis.asyncio import Redis
from shared.db.mongo import connect_mongo
from shared.redis.connection import connect_redis

from src.settings import settings


async def connect_databases() -> tuple[AsyncMongoClient, AsyncDatabase, Redis]:
    mongo_client, database = await connect_mongo(settings.mongo_url, settings.mongo_db)
    redis_client = await connect_redis(settings.redis_url)
    return mongo_client, database, redis_client


async def close_databases(*, mongo_client: AsyncMongoClient | None = None, redis_client: Redis | None = None) -> None:
    if redis_client:
        await redis_client.close()
    if mongo_client:
        await mongo_client.close()
