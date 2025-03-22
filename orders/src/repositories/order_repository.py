from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClientSession, AsyncIOMotorCollection
from redis.asyncio import Redis

from src.interfaces import IOrderRepository
from src.schemas import OrderSchema, OrderStatus


class OrderRepository(IOrderRepository):
    def __init__(self, collection: AsyncIOMotorCollection, redis_client: Redis):
        self._collection = collection
        self._redis = redis_client

    async def create(self, order_data: OrderSchema, session: AsyncIOMotorClientSession) -> str:
        doc = order_data.model_dump(by_alias=True, exclude={"id"}, mode="json")
        result = await self._collection.insert_one(doc, session=session)
        return str(result.inserted_id)

    async def get(self, order_id: str, session: AsyncIOMotorClientSession | None) -> Optional[OrderSchema]:
        doc = await self._collection.find_one({"_id": ObjectId(order_id)})
        return OrderSchema(**doc) if doc else None

    async def update_status(self, order_id: str, new_status: OrderStatus, session: AsyncIOMotorClientSession) -> bool:
        result = await self._collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": new_status.value}},
            session=session,
        )
        return bool(result.modified_count)
