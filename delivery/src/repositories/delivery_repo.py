import asyncio
import json
import logging
from typing import AsyncGenerator, Final

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from redis.asyncio import Redis

from src.schemas import DeliverySchema, DeliveryStatus


class DeliveryRepository:
    OUT_OF_DELIVERY_STATUS: Final = "out_for_delivery"

    def __init__(self, collection: AsyncIOMotorCollection, redis_client: Redis):
        self._collection = collection
        self._redis = redis_client

    async def create_delivery(self, delivery_data: DeliverySchema) -> str:
        doc = delivery_data.model_dump(by_alias=True, exclude={"id"})
        result = await self._collection.insert_one(doc)
        return str(result.inserted_id)

    async def get_delivery(self, delivery_id: str) -> DeliverySchema:
        delivery = await self._collection.find_one({"_id": ObjectId(delivery_id)})
        return DeliverySchema(**delivery)

    async def get_delivery_by_order_id(self, order_id: str) -> DeliverySchema:
        delivery = await self._collection.find_one({"order_id": order_id})
        return DeliverySchema(**delivery)

    async def update_delivery_status(self, delivery_id: str, new_status: DeliveryStatus) -> bool:
        result = await self._collection.update_one(
            {"_id": ObjectId(delivery_id)}, {"$set": {"status": new_status.value}}
        )
        return bool(result.modified_count)

    async def update_and_publish_delivery_status(self, *, delivery_id: str, new_status: DeliveryStatus) -> bool:
        updated = await self.update_delivery_status(delivery_id, new_status)
        if not updated:
            return False
        if delivery_ := await self._collection.find_one({"_id": ObjectId(delivery_id)}):
            await self.publish_delivery_status(DeliverySchema(**delivery_))
        return updated

    async def publish_delivery_status(self, delivery_data: DeliverySchema) -> None:
        data = json.dumps(delivery_data.model_dump(mode="json"))
        logging.info(f"📡 Streaming order: {data}")
        await self._redis.xadd("deliveries_stream", {"data": data})

    async def trigger_delivery_simulation(self, order_data: dict) -> None:
        event = json.dumps(order_data)
        await self._redis.xadd("simulate_delivery_stream", {"data": event})

    async def get_last_stream_id(self, stream_name: str) -> str:
        return await self._redis.get(f"last_id:{stream_name}") or "0-0"

    async def read_stream(
        self, stream_name: str, block: int = 5000, count: int = 10
    ) -> AsyncGenerator[tuple[str, dict], None]:
        last_id = await self.get_last_stream_id(stream_name)

        while True:
            try:
                streams = await self._redis.xread({stream_name: last_id}, block=block, count=count)
                if not streams:
                    await asyncio.sleep(1)
                    continue

                for _, messages in streams:
                    for message_id, message_data in messages:
                        yield message_id, message_data

                        await self._redis.set(f"last_id:{stream_name}", message_id)

                        last_id = message_id

            except Exception as e:
                logging.error(f"Error reading Redis stream {stream_name}: {e}")
                await asyncio.sleep(1)

    async def subscribe_to_orders(self) -> None:
        async for message_id, message_data in self.read_stream("orders_stream"):
            order_data = json.loads(message_data["data"])
            order_status = order_data.get("status")

            if order_status != self.OUT_OF_DELIVERY_STATUS:
                continue

            delivery_doc = DeliverySchema(order_id=order_data.get("id"))
            doc_id = await self.create_delivery(delivery_doc)
            logging.info(f"Delivery created for order: {doc_id}")
            await self.publish_delivery_status(delivery_doc)

            if order_data.get("simulator") != -1:
                await self.trigger_delivery_simulation(order_data)
                logging.info(f"Simulating delivery for: {doc_id}")

    async def subscribe_to_status_changes(self) -> None:
        async for message_id, message in self.read_stream("delivery_status_stream"):
            try:
                message_data = json.loads(message["data"])
                logging.info(f"Delivery status received for {message_data}")
                if (
                    delivery_doc := await self.get_delivery_by_order_id(message_data["id"])
                ) and delivery_doc.id is not None:
                    await self.update_and_publish_delivery_status(
                        delivery_id=delivery_doc.id, new_status=DeliveryStatus(message_data["status"])
                    )
            except Exception as e:
                logging.error(f"Error processing `delivery_status_stream`: {message}, error: {e}")
                continue
