from fastapi import FastAPI

from src.config import settings
from src.database.redis_connection import connect_redis


async def setup_redis(app: FastAPI) -> None:
    app.state.redis_client = await connect_redis(settings.redis_url)


async def close_redis(app: FastAPI) -> None:
    if redis := getattr(app.state, "redis_client", None):
        await redis.close()


__all__ = ["setup_redis", "close_redis"]
