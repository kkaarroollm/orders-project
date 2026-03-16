import logging
from typing import Any

from src.repository import NotificationRepository
from src.schemas import CacheSchema
from src.websockets import OrderStatusConnectionManager


class NotificationService:
    def __init__(self, repo: NotificationRepository, ws_manager: OrderStatusConnectionManager) -> None:
        self._repo = repo
        self._ws_manager = ws_manager

    async def handle_event(self, msg: Any) -> None:
        order_id = getattr(msg, "order_id", None) or getattr(msg, "id", None)
        status = getattr(msg, "status", None)
        if not (order_id and status):
            raise ValueError(f"NotificationService.handle_event: Invalid data received: {msg}")

        cache = CacheSchema(order_id=order_id, status=status).model_dump(mode="json")

        logging.info("Update for order %s: %s", order_id, status)

        await self._ws_manager.broadcast(order_id, cache)
        await self._repo.set_order_status(order_id, cache)
