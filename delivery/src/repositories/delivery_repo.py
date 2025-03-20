import asyncio
import json
import logging
from typing import Final

from motor.motor_asyncio import AsyncIOMotorCollection
from redis.asyncio import Redis

from src.schemas import CourierSchema, DeliverySchema, DeliveryStatus
from bson import ObjectId


class DeliveryRepository:
    OUT_OF_DELIVERY_STATUS: Final = "out_for_delivery"

    def __init__(self, collection: AsyncIOMotorCollection, redis_client: Redis):
        self._collection = collection
        self._redis = redis_client
        self._active_tasks: set[asyncio.Task] = set()

    @property
    def active_tasks(self) -> set[asyncio.Task]:
        return self._active_tasks

    async def create_delivery(self, delivery_data: DeliverySchema) -> str:
        doc = delivery_data.model_dump(by_alias=True, exclude={"id"})
        result = await self._collection.insert_one(doc)
        return str(result.inserted_id)

    async def update_delivery_status(self, delivery_id: str, new_status: DeliveryStatus) -> bool:
        result = await self._collection.update_one(
            {"_id": ObjectId(delivery_id)},
            {"$set": {"status": new_status.value}}
        )
        return result.modified_count > 0

    async def _simulate_delivery(self, delivery_id: str) -> None:
        """Method to simulate the delivery process."""
        try:
            await asyncio.sleep(120)
            await self.update_and_publish_delivery_status(delivery_id, DeliveryStatus.ON_THE_WAY)
            await asyncio.sleep(200)
            await self.update_and_publish_delivery_status(delivery_id, DeliveryStatus.DELIVERED)
            logging.info(f"Order {delivery_id} has been DELIVERED!")
        except asyncio.CancelledError:
            logging.warning(f"Delivery simulation for {delivery_id} has been cancelled.")
        finally:
            self._active_tasks.discard(asyncio.current_task())


    async def update_and_publish_delivery_status(self, delivery_id: str, new_status: DeliveryStatus) -> bool:
        updated = await self.update_delivery_status(delivery_id, new_status)
        if not updated:
            return False
        if delivery_ := await self._collection.find_one({"_id": ObjectId(delivery_id)}):
            await self.publish_delivery_status(DeliverySchema(**delivery_))
        return updated

    async def publish_delivery_status(self, delivery_data: DeliverySchema) -> None:
        data = json.dumps(delivery_data.model_dump(mode="json"))
        logging.info(f"📡 Publishing order: {data}")
        await self._redis.publish("delivery_channel", data)

    async def subscribe_to_orders(self) -> None:
        pubsub = self._redis.pubsub()
        await pubsub.subscribe("orders_channel")

        async for message in pubsub.listen():
            if message["type"] == "message":
                order_data = json.loads(message["data"])
                order_status = order_data.get("status")

                if order_status != self.OUT_OF_DELIVERY_STATUS:
                    continue

                delivery_doc = DeliverySchema(order_id=order_data.get("id"))
                doc_id = await self.create_delivery(delivery_doc)
                logging.info(f"Delivery created for order: {doc_id}")
                await self.publish_delivery_status(delivery_doc)

                simulator_task = asyncio.create_task(self._simulate_delivery(doc_id))
                self._active_tasks.add(simulator_task)

                logging.info(f"Simulating delivery for: {doc_id}")
