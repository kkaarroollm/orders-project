import asyncio
import logging
import os
import signal
import socket
import uuid
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from redis.asyncio import Redis

from shared.events.base import DomainEvent
from shared.redis.consumer import Route, StreamConsumer

T = TypeVar("T", bound=DomainEvent)

ConsumerFailureHandler = Callable[[str, BaseException], None]


def terminate_on_failure(group: str, error: BaseException) -> None:
    """Default failure policy: stop the process so the orchestrator restarts it.

    A consumer that dies silently leaves the pod Ready and serving HTTP while no
    events are processed at all. Restarting is honest; retry-with-backoff inside
    the process would hide the failure.
    """
    logging.critical("Consumer group `%s` died, terminating process: %s", group, error)
    os.kill(os.getpid(), signal.SIGTERM)


class EventBus:
    """Manages stream subscriptions with retry, DLQ, and graceful lifecycle."""

    def __init__(
        self,
        redis: Redis,
        *,
        group: str,
        max_retries: int = 3,
        dlq_stream: str | None = "dead-letters",
        on_consumer_failure: ConsumerFailureHandler | None = terminate_on_failure,
    ) -> None:
        self._redis = redis
        self._group = group
        self._max_retries = max_retries
        self._dlq_stream = dlq_stream
        self._on_consumer_failure = on_consumer_failure
        self._consumer_name = f"{group}-{socket.gethostname()}-{uuid.uuid4().hex[:6]}"
        self._routes: dict[str, dict[str, Route[Any]]] = defaultdict(dict)
        self._tasks: list[asyncio.Task[None]] = []
        self._healthy = True

    @property
    def healthy(self) -> bool:
        """False once any consumer task has died; readiness probes read this."""
        return self._healthy

    def subscribe(self, event: type[T], handler: Callable[[T], Awaitable[None]]) -> None:
        """Route one event class to a handler.

        The stream and wire type come from the event class, so no call site
        repeats a stream string, and the handler's parameter type is checked
        against the event it is registered for.
        """
        route = Route(event=event, handler=handler)
        for wire_type in (event.event_type, *event.legacy_types):
            self._routes[event.stream][wire_type] = route

    async def start(self) -> None:
        for stream, routes in self._routes.items():
            consumer = StreamConsumer(
                redis=self._redis,
                stream=stream,
                group=self._group,
                consumer_name=self._consumer_name,
                routes=routes,
                max_retries=self._max_retries,
                dlq_stream=self._dlq_stream,
            )
            task = asyncio.create_task(consumer.listen())
            task.add_done_callback(self._on_task_done)
            self._tasks.append(task)

        logging.info(
            "EventBus started: %d stream consumer(s) in group '%s'",
            len(self._tasks),
            self._group,
        )

    def _on_task_done(self, task: asyncio.Task[None]) -> None:
        """`listen()` loops forever, so any completion at all is a failure."""
        if task.cancelled():
            return  # expected during stop()

        error = task.exception() or RuntimeError("stream consumer exited without raising")
        self._healthy = False
        logging.critical("EventBus consumer in group `%s` stopped: %s", self._group, error)

        if self._on_consumer_failure:
            self._on_consumer_failure(self._group, error)

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
