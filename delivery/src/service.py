import logging
from typing import Any, Final

from shared.events.base import OrderEvent
from shared.events.delivery import (
    DeliveryCreated,
    DeliverySimulationRequested,
    DeliveryStatusChanged,
    DeliveryStatusSimulated,
)
from shared.redis.publisher import StreamProducer

from src.repository import DeliveryRepository
from src.schemas import DeliverySchema, DeliveryStatus


class DeliveryService:
    OUT_FOR_DELIVERY: Final = "out_for_delivery"

    def __init__(self, repo: DeliveryRepository, publisher: StreamProducer[Any]) -> None:
        self._repo = repo
        self._publisher = publisher

    async def handle_order(self, event: OrderEvent) -> None:
        if event.status != self.OUT_FOR_DELIVERY:
            logging.info("Skipping order %s, status not '%s'", event.id, self.OUT_FOR_DELIVERY)
            return

        delivery = DeliverySchema(order_id=event.id)
        delivery_id = await self._repo.create(delivery)
        logging.info("Created delivery %s", delivery_id)

        await self._publisher.publish(
            DeliveryCreated(order_id=event.id, status=delivery.status.value),
            correlation_id=event.id,
        )

        if event.simulation != -1:
            await self._publisher.publish(
                DeliverySimulationRequested(id=event.id),
                correlation_id=event.id,
            )
            logging.info("Simulating delivery for %s", delivery_id)

    async def handle_status_update(self, event: DeliveryStatusSimulated) -> None:
        order_id = event.id
        delivery = await self._repo.find_one({"order_id": order_id})

        if not (delivery and delivery.id):
            raise ValueError(f"DeliveryService.handle_status_update: Delivery not found for order_id {order_id}")

        new_status = DeliveryStatus(event.status)

        if await self._repo.update_status(delivery.id, new_status):
            await self._publisher.publish(
                DeliveryStatusChanged(order_id=order_id, status=new_status.value),
                correlation_id=order_id,
            )
