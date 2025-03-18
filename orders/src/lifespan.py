import logging
import os

from fastapi import FastAPI
from redis.asyncio import Redis

from src.common import setup_logging
from src.database import connect_mongo, connect_redis


async def startup(app: FastAPI) -> None:
    """Startup sequence: Connect to DB & initialize resources."""
    app.state.ready = False
    setup_logging()

    mongo_client, db = await connect_mongo(os.getenv("MONGO_URL", "default"))
    app.state.mongo_client = mongo_client
    app.state.db = db

    redis_client: Redis = await connect_redis()
    app.state.redis_client = redis_client
    app.state.ready = True
    logging.info("Orders service is ready.")


async def teardown(app: FastAPI) -> None:
    """Teardown sequence: Close DB connections & cleanup resources."""
    app.state.ready = False

    if redis_client := getattr(app.state, "redis_client"):
        await redis_client.close()

    if mongo_client := getattr(app.state, "mongo_client"):
        mongo_client.close()

    logging.info("Orders service is shut down.")
