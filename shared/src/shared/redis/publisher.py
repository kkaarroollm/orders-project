import json
import logging
import time
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from redis.asyncio import Redis

TMessage = TypeVar("TMessage", bound=BaseModel)


class StreamProducer(Generic[TMessage]):
    def __init__(self, redis: Redis, *, source: str = "") -> None:
        self._redis = redis
        self._source = source

    async def publish(self, stream: str, message: TMessage, *, event_type: str = "", correlation_id: str = "") -> None:
        try:
            data = message.model_dump(mode="json")
            effective_id = correlation_id or data.get("id", "")
            envelope = self._wrap(data, event_type=event_type, correlation_id=effective_id)
            await self._redis.xadd(stream, {"data": json.dumps(envelope)})
            logging.info("Published to `%s`: event=%s correlation=%s", stream, event_type, effective_id)
        except Exception as e:
            logging.error("Failed to publish to Redis stream `%s`: %s", stream, e)

    async def publish_raw(
        self,
        stream: str,
        data: dict[str, Any],
        *,
        event_type: str = "",
        correlation_id: str = "",
    ) -> None:
        try:
            effective_id = correlation_id or data.get("id", "")
            envelope = self._wrap(data, event_type=event_type, correlation_id=effective_id)
            await self._redis.xadd(stream, {"data": json.dumps(envelope)})
            logging.info("Published to `%s`: event=%s correlation=%s", stream, event_type, effective_id)
        except Exception as e:
            logging.error("Failed to publish to Redis stream `%s`: %s", stream, e)

    def _wrap(self, data: dict[str, Any], *, event_type: str, correlation_id: str) -> dict[str, Any]:
        return {
            "event_type": event_type,
            "correlation_id": correlation_id,
            "source": self._source,
            "timestamp": time.time(),
            "payload": data,
        }
