import asyncio
import logging
import socket
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from redis.asyncio import Redis

from shared.redis.consumer import StreamConsumer

T = TypeVar("T", bound=BaseModel)


@dataclass
class _Subscription(Generic[T]):
    stream: str
    model: type[T]
    handler: Callable[[T], Awaitable[None]]


class EventBus:
    """Manages stream subscriptions with retry, DLQ, and graceful lifecycle."""

    def __init__(
        self,
        redis: Redis,
        *,
        group: str,
        max_retries: int = 3,
        dlq_stream: str | None = "dead-letters",
    ) -> None:
        self._redis = redis
        self._group = group
        self._max_retries = max_retries
        self._dlq_stream = dlq_stream
        self._consumer_name = f"{group}-{socket.gethostname()}-{uuid.uuid4().hex[:6]}"
        self._subscriptions: list[_Subscription[Any]] = []
        self._tasks: list[asyncio.Task[None]] = []

    def subscribe(self, stream: str, model: type[T], handler: Callable[[T], Awaitable[None]]) -> None:
        self._subscriptions.append(_Subscription(stream=stream, model=model, handler=handler))

    async def start(self) -> None:
        for sub in self._subscriptions:
            consumer: StreamConsumer[Any] = StreamConsumer(
                redis=self._redis,
                stream=sub.stream,
                group=self._group,
                consumer_name=self._consumer_name,
                message_type=sub.model,
                max_retries=self._max_retries,
                dlq_stream=self._dlq_stream,
            )
            task = asyncio.create_task(consumer.listen(sub.handler))
            self._tasks.append(task)

        logging.info(
            "EventBus started: %d subscription(s) in group '%s'",
            len(self._tasks),
            self._group,
        )

    async def run_forever(self) -> None:
        """Start all consumers and block until they complete or are cancelled."""
        await self.start()
        await asyncio.gather(*self._tasks)

    async def stop(self) -> None:
        for task in self._tasks:
            if not task.done():
                task.cancel()

        results = await asyncio.gather(*self._tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                logging.error("EventBus task error during shutdown: %s", result)

        self._tasks.clear()
        logging.info("EventBus stopped for group '%s'", self._group)
