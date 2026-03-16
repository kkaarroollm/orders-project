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

    async def handle_order(self, msg: Any) -> None:
        if msg.status != self.OUT_FOR_DELIVERY:
            logging.info("Skipping order %s, status not '%s'", msg.id, self.OUT_FOR_DELIVERY)
            return

        delivery = DeliverySchema(order_id=msg.id)
        delivery_id = await self._repo.create(delivery)
        logging.info("Created delivery %s", delivery_id)

        await self._publisher.publish_raw(settings.deliveries_stream, delivery.model_dump(mode="json"))

        if getattr(msg, "simulation", 1) != -1:
            await self._publisher.publish_raw(settings.simulate_delivery_stream, msg.model_dump(mode="json"))
            logging.info("Simulating delivery for %s", delivery_id)

    async def handle_status_update(self, msg: Any) -> None:
        order_id = getattr(msg, "order_id", None) or msg.id
        if not order_id:
            raise ValueError("DeliveryService.handle_status_update: Missing order_id in status update")

        delivery = await self._repo.find_one({"order_id": order_id})

        if not (delivery and delivery.id):
            raise ValueError(f"DeliveryService.handle_status_update: Delivery not found for order_id {order_id}")

        new_status = DeliveryStatus(msg.status)

        if await self._repo.update_status(delivery.id, new_status):
            delivery.status = new_status
            await self._publisher.publish_raw(settings.deliveries_stream, delivery.model_dump(mode="json"))
