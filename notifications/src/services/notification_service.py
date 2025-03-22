import logging

from src.interfaces import INotificationRepository, INotificationService, IOrderStatusConnectionManager
from src.schemas import CacheSchema


class NotificationService(INotificationService):
    def __init__(self, repo: INotificationRepository, ws_manager: IOrderStatusConnectionManager) -> None:
        self._repo = repo
        self._ws_manager = ws_manager

    async def handle_event(self, data: dict) -> None:
        order_id = data.get("order_id") or data.get("id")
        status = data.get("status")
        if not (order_id and status):
            raise ValueError(f"NotificationService.handle_event: Invalid data received: {data}")

        cache = CacheSchema(order_id=order_id, status=status).model_dump(mode="json")

        logging.info(f" Update for order {order_id}: {status}")

        await self._ws_manager.broadcast(order_id, cache)
        await self._repo.set_order_status(order_id, cache)
