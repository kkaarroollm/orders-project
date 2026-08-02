import logging
from typing import Any

from shared.events.base import DeliveryEvent, OrderEvent
from shared.events.notifications import OrderStatusPush
from shared.redis.publisher import StreamProducer

from src.repository import NotificationRepository
from src.schemas import CacheSchema
from src.sse import OrderStreamRegistry


class NotificationService:
    """Turns domain events into a cached snapshot plus a fanned-out push.

    The domain streams are read by one shared consumer group, so a single
    replica sees each event -- but the client's SSE stream may be held by any
    replica. Re-publishing onto the fanout stream is what bridges that gap.
    """

    def __init__(self, repo: NotificationRepository, producer: StreamProducer[Any]) -> None:
        self._repo = repo
        self._producer = producer

    async def handle_order_event(self, event: OrderEvent) -> None:
        await self._push(event.order_id, event.status)

    async def handle_delivery_event(self, event: DeliveryEvent) -> None:
        await self._push(event.order_id, event.status)

    async def _push(self, order_id: str, status: str) -> None:
        payload = CacheSchema(order_id=order_id, status=status).model_dump(mode="json")

        logging.info("Update for order %s: %s", order_id, status)

        # Snapshot first: a client that connects a moment later reads it, so a
        # push nobody was listening for is self-healing.
        await self._repo.set_order_status(order_id, payload)
        await self._producer.publish(
            OrderStatusPush(order_id=order_id, status=status, timestamp=payload["timestamp"]),
            correlation_id=order_id,
        )


class StatusPushFanout:
    """Delivers a fanned-out push to the clients held by *this* replica."""

    def __init__(self, registry: OrderStreamRegistry) -> None:
        self._registry = registry

    async def handle_push(self, event: OrderStatusPush) -> None:
        await self._registry.broadcast(
            event.order_id,
            {"order_id": event.order_id, "status": event.status, "timestamp": event.timestamp},
        )
