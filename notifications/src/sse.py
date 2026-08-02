import asyncio
import json
import logging
import random
from collections.abc import AsyncGenerator
from typing import Any

KEEPALIVE_SECONDS = 25
_QUEUE_MAXSIZE = 32

# Reconnect delay handed to the browser. Randomised per connection so clients
# do not reconnect in lockstep after a rollout.
_RETRY_MIN_MS = 2_000
_RETRY_MAX_MS = 6_000

_SHUTDOWN = object()


class OrderStreamRegistry:
    """Per-connection queues keyed by order id.

    One queue per open response rather than one socket per client: the SSE
    endpoint is a generator, so delivery is a queue put instead of a send.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[Any]]] = {}

    def subscribe(self, order_id: str) -> asyncio.Queue[Any]:
        queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=_QUEUE_MAXSIZE)
        self._subscribers.setdefault(order_id, []).append(queue)
        logging.info("Client subscribed to order %s", order_id)
        return queue

    def unsubscribe(self, order_id: str, queue: asyncio.Queue[Any]) -> None:
        queues = self._subscribers.get(order_id)
        if not queues:
            return
        if queue in queues:
            queues.remove(queue)
        if not queues:
            del self._subscribers[order_id]
        logging.info("Client unsubscribed from order %s", order_id)

    async def broadcast(self, order_id: str, message: dict[str, Any]) -> None:
        for queue in self._subscribers.get(order_id, []):
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                # A client too slow to drain 32 status updates is not worth
                # blocking the consumer for; it re-syncs from the snapshot.
                logging.warning("Dropping update for order %s: subscriber queue full", order_id)
        logging.info("Broadcast update for order %s: %s", order_id, message)

    async def close_all(self) -> None:
        """End every open stream so clients reconnect instead of hanging."""
        for queues in list(self._subscribers.values()):
            for queue in queues:
                try:
                    queue.put_nowait(_SHUTDOWN)
                except asyncio.QueueFull:
                    pass
        self._subscribers.clear()


def format_event(message: dict[str, Any]) -> str:
    return f"id: {message.get('timestamp', '')}\ndata: {json.dumps(message)}\n\n"


async def event_stream(
    registry: OrderStreamRegistry,
    order_id: str,
    snapshot: dict[str, Any] | None,
) -> AsyncGenerator[str]:
    queue = registry.subscribe(order_id)
    try:
        yield f"retry: {random.randint(_RETRY_MIN_MS, _RETRY_MAX_MS)}\n\n"

        # Current status first, so a reconnecting client is never left blank
        # while it waits for the next transition.
        if snapshot:
            yield format_event(snapshot)

        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=KEEPALIVE_SECONDS)
            except TimeoutError:
                yield ": keepalive\n\n"
                continue

            if message is _SHUTDOWN:
                return
            yield format_event(message)
    finally:
        registry.unsubscribe(order_id, queue)


order_stream_registry: OrderStreamRegistry = OrderStreamRegistry()
