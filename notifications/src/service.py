import logging

from shared.events.base import DeliveryEvent, OrderEvent

from src.repository import NotificationRepository
from src.schemas import CacheSchema
from src.sse import OrderStreamRegistry


class NotificationService:
    def __init__(self, repo: NotificationRepository, registry: OrderStreamRegistry) -> None:
        self._repo = repo
        self._registry = registry

    async def handle_order_event(self, event: OrderEvent) -> None:
        await self._push(event.order_id, event.status)

    async def handle_delivery_event(self, event: DeliveryEvent) -> None:
        await self._push(event.order_id, event.status)

    async def _push(self, order_id: str, status: str) -> None:
        cache = CacheSchema(order_id=order_id, status=status).model_dump(mode="json")

        logging.info("Update for order %s: %s", order_id, status)

        await self._registry.broadcast(order_id, cache)
        await self._repo.set_order_status(order_id, cache)
