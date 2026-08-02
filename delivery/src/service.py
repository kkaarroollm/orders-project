import logging
from typing import Any, Final

from pymongo import AsyncMongoClient
from pymongo.errors import DuplicateKeyError
from shared.db.inbox import MongoInbox
from shared.db.mongo import MongoTransactionManager
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
from src.settings import settings


class DeliveryService:
    OUT_FOR_DELIVERY: Final = "out_for_delivery"

    def __init__(
        self,
        repo: DeliveryRepository,
        publisher: StreamProducer[Any],
        inbox: MongoInbox,
        mongo_client: AsyncMongoClient,
    ) -> None:
        self._repo = repo
        self._publisher = publisher
        self._inbox = inbox
        self._mongo_client = mongo_client

    async def handle_order(self, event: OrderEvent) -> None:
        if event.status != self.OUT_FOR_DELIVERY:
            logging.info("Skipping order %s, status not '%s'", event.id, self.OUT_FOR_DELIVERY)
            return

        delivery = DeliverySchema(order_id=event.id)
        if not await self._create_once(event.event_id, delivery):
            logging.info("Delivery for order %s already created, skipping duplicate", event.id)
            return

        logging.info("Created delivery for order %s", event.id)

        await self._publisher.publish(
            DeliveryCreated(order_id=event.id, status=delivery.status.value),
            correlation_id=event.id,
        )

        if event.simulation != -1:
            await self._publisher.publish(
                DeliverySimulationRequested(id=event.id),
                correlation_id=event.id,
            )
            logging.info("Simulating delivery for order %s", event.id)

    async def _create_once(self, event_id: str, delivery: DeliverySchema) -> bool:
        """Create the delivery unless this event was already applied.

        The inbox insert shares the transaction with the create, so a redelivery
        hits the unique index, aborts the whole transaction, and leaves no
        second delivery behind.
        """
        try:
            async with MongoTransactionManager(self._mongo_client) as session:
                await self._inbox.record(settings.delivery_group, event_id, session)
                await self._repo.create(delivery, session)
        except DuplicateKeyError:
            return False
        return True

    async def handle_status_update(self, event: DeliveryStatusSimulated) -> None:
        order_id = event.id
        delivery = await self._repo.find_one({"order_id": order_id})

        if not (delivery and delivery.id):
            raise ValueError(f"DeliveryService.handle_status_update: Delivery not found for order_id {order_id}")

        new_status = DeliveryStatus(event.status)

        # Idempotent by construction: applying the same status twice is a no-op.
        if await self._repo.update_status(delivery.id, new_status):
            await self._publisher.publish(
                DeliveryStatusChanged(order_id=order_id, status=new_status.value),
                correlation_id=order_id,
            )
