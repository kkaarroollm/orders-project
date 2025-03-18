import json
import logging

from motor.motor_asyncio import AsyncIOMotorCollection
from redis.asyncio import Redis

from src.schemas import CourierSchema, DeliverySchema, DeliveryStatus


class DeliveryRepository:
    def __init__(self, collection: AsyncIOMotorCollection, redis_client: Redis):
        self._collection = collection
        self._redis = redis_client

    async def create_delivery(self, delivery_data: DeliverySchema) -> str:
        doc = delivery_data.model_dump(by_alias=True, exclude={"id"})
        result = await self._collection.insert_one(doc)
        return str(result.inserted_id)

    async def publish_delivery_started(self, delivery_data: DeliverySchema) -> None:
        data = json.dumps(delivery_data.model_dump(by_alias=True))
        await self._redis.publish("delivery_channel", data)

    async def subscribe_to_orders(self) -> None:
        pubsub = self._redis.pubsub()
        await pubsub.subscribe("orders_channel")

        async for message in pubsub.listen():
            logging.info(f"📡 Received message: {message}")
            if message["type"] == "message":
                order_data = json.loads(message["data"])
                logging.info(f"📦 Processing order: {order_data}")

                ### MOCK DATA
                random_courier = CourierSchema(first_name="Lechu", last_name="K", phone_number="1234567890")
                order_data["courier"] = random_courier
                order_data["status"] = DeliveryStatus.ON_THE_WAY
                order_data["order_id"] = order_data.pop("_id")
                ###

                delivery_doc = DeliverySchema(**order_data)

                await self.create_delivery(delivery_doc)
                await self.publish_delivery_started(delivery_doc)
