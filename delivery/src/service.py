import logging
from typing import Any, Final

from shared.redis.publisher import StreamProducer

from src.repository import DeliveryRepository
from src.schemas import DeliverySchema, DeliveryStatus
from src.settings import settings


class DeliveryService:
    OUT_FOR_DELIVERY: Final = "out_for_delivery"

    def __init__(self, repo: DeliveryRepository, publisher: StreamProducer[Any]) -> None:
        self._repo = repo
        self._publisher = publisher

    async def handle_order(self, order_data: dict[str, Any]) -> None:
        if order_data.get("status") != self.OUT_FOR_DELIVERY:
            logging.info("Skipping order %s, status not '%s'", order_data.get("id"), self.OUT_FOR_DELIVERY)
            return

        delivery = DeliverySchema(order_id=order_data["id"])
        delivery_id = await self._repo.create(delivery)
        logging.info("Created delivery %s", delivery_id)

        await self._publisher.publish_raw(settings.deliveries_stream, delivery.model_dump(mode="json"))

        if order_data.get("simulator") != -1:
            await self._publisher.publish_raw(settings.simulate_delivery_stream, order_data)
            logging.info("Simulating delivery for %s", delivery_id)

    async def handle_status_update(self, status_data: dict[str, Any]) -> None:
        if not (order_id := status_data.get("order_id") or status_data.get("id")):
            raise ValueError("DeliveryService.handle_status_update: Missing order_id in status update")

        delivery = await self._repo.find_one({"order_id": order_id})

        if not (delivery and delivery.id):
            raise ValueError(f"DeliveryService.handle_status_update: Delivery not found for order_id {order_id}")

        new_status = DeliveryStatus(status_data["status"])

        if await self._repo.update_status(delivery.id, new_status):
            delivery.status = new_status
            await self._publisher.publish_raw(settings.deliveries_stream, delivery.model_dump(mode="json"))
