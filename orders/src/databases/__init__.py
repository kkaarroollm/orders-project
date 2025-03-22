from fastapi import FastAPI

from src.config import settings
from src.databases.connections import connect_mongo, connect_redis
from src.databases.mongo_transaction import MongoDBTransactionManager


async def setup_databases(app: FastAPI) -> None:
    app.state.mongo_client, app.state.database = await connect_mongo(settings.mongo_url, settings.mongo_db)
    app.state.redis_client = await connect_redis(settings.redis_url)


async def close_databases(app: FastAPI) -> None:
    if redis := getattr(app.state, "redis_client", None):
        await redis.close()
    if mongo := getattr(app.state, "mongo_client", None):
        mongo.close()


__all__ = ["setup_databases", "close_databases"]
