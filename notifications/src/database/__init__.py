from fastapi import FastAPI
from shared.redis.connection import connect_redis

from src.config import settings


async def setup_redis(app: FastAPI) -> None:
    app.state.redis_client = await connect_redis(settings.redis_url)


async def close_redis(app: FastAPI) -> None:
    if redis := getattr(app.state, "redis_client", None):
        await redis.close()


__all__ = ["setup_redis", "close_redis"]
