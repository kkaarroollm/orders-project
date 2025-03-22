import logging
from typing import Final

from src.config import settings
from src.interfaces import IDeliveryRepository, IDeliveryService, IRedisStreamPublisher
from src.schemas import DeliverySchema, DeliveryStatus


class DeliveryService(IDeliveryService):
    OUT_FOR_DELIVERY: Final = "out_for_delivery"

    def __init__(self, repo: IDeliveryRepository, publisher: IRedisStreamPublisher):
        self._repo = repo
        self._publisher = publisher

    async def handle_order(self, order_data: dict) -> None:
        """Note: This is a mock implementation."""
        if order_data.get("status") != self.OUT_FOR_DELIVERY:
            logging.debug(f"Skipping order {order_data.get("id")}, status not '{self.OUT_FOR_DELIVERY}'")
            return

        delivery = DeliverySchema(order_id=order_data["id"])
        delivery_id = await self._repo.create(delivery)
        logging.info(f"Created delivery {delivery_id}")

        await self._publisher.publish(settings.deliveries_stream, delivery.model_dump(mode="json"))

        if order_data.get("simulator") != -1:
            await self._publisher.publish(settings.simulate_delivery_stream, order_data)
            logging.info(f"Simulating delivery for {delivery_id}")

    async def handle_status_update(self, status_data: dict) -> None:
        if not (order_id := status_data.get("order_id")):
            raise ValueError("DeliveryService.handle_status_update: Missing order_id in status update")

        delivery = await self._repo.get_by_order_id(order_id)

        if not (delivery and delivery.id):
            raise ValueError(f"DeliveryService.handle_status_update: Delivery not found for order_id {order_id}")

        new_status = DeliveryStatus(status_data["status"])

        if await self._repo.update_status(delivery.id, new_status):
            delivery.status = new_status
            await self._publisher.publish(settings.deliveries_stream, delivery.model_dump(mode="json"))
