import json
import logging
import time
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from redis.asyncio import Redis

from shared.events.base import DomainEvent

TMessage = TypeVar("TMessage", bound=BaseModel)

_DEFAULT_MAXLEN = 100_000


class StreamProducer(Generic[TMessage]):
    """Publishes enveloped events to a Redis stream.

    Publish failures are raised, never swallowed: a caller that believes it
    published an event it did not is worse than a caller that fails loudly.
    """

    def __init__(self, redis: Redis, *, source: str = "", maxlen: int = _DEFAULT_MAXLEN) -> None:
        self._redis = redis
        self._source = source
        self._maxlen = maxlen

    async def publish(self, event: DomainEvent, *, correlation_id: str = "") -> None:
        """Publish a typed event; its class supplies the stream and wire type."""
        await self.publish_raw(
            event.stream,
            event.model_dump(mode="json"),
            event_type=event.event_type,
            correlation_id=correlation_id,
        )

    async def publish_raw(
        self,
        stream: str,
        data: dict[str, Any],
        *,
        event_type: str = "",
        correlation_id: str = "",
    ) -> None:
        effective_id = correlation_id or data.get("id", "")
        envelope = self._wrap(data, event_type=event_type, correlation_id=effective_id)
        # Approximate trimming keeps stream memory bounded without the cost of
        # exact trimming on every write.
        await self._redis.xadd(
            stream,
            {"data": json.dumps(envelope)},
            maxlen=self._maxlen,
            approximate=True,
        )
        logging.info("Published to `%s`: event=%s correlation=%s", stream, event_type, effective_id)

    def _wrap(self, data: dict[str, Any], *, event_type: str, correlation_id: str) -> dict[str, Any]:
        return {
            "event_type": event_type,
            "correlation_id": correlation_id,
            "source": self._source,
            "timestamp": time.time(),
            "payload": data,
        }
