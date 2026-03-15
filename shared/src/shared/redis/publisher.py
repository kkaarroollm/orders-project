import json
import logging
from typing import Generic, TypeVar

from pydantic import BaseModel
from redis.asyncio import Redis

TMessage = TypeVar("TMessage", bound=BaseModel)


class StreamProducer(Generic[TMessage]):
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def publish(self, stream: str, message: TMessage) -> None:
        try:
            data = message.model_dump(mode="json")
            await self._redis.xadd(stream, {"data": json.dumps(data)})
            logging.info("Published to stream `%s`: %s", stream, data)
        except Exception as e:
            logging.error("Failed to publish to Redis stream `%s`: %s", stream, e)

    async def publish_raw(self, stream: str, data: dict) -> None:  # type: ignore[type-arg]
        try:
            await self._redis.xadd(stream, {"data": json.dumps(data)})
            logging.info("Published to stream `%s`: %s", stream, data)
        except Exception as e:
            logging.error("Failed to publish to Redis stream `%s`: %s", stream, e)
