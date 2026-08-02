from bson import ObjectId
from pymongo.asynchronous.collection import AsyncCollection
from shared.db.repository import MongoRepository

from src.schemas import ALLOWED_PREVIOUS, DeliverySchema, DeliveryStatus


class DeliveryRepository(MongoRepository[DeliverySchema]):
    def __init__(self, collection: AsyncCollection) -> None:
        super().__init__(collection, DeliverySchema)

    async def ensure_indexes(self) -> None:
        """Back `get_by_order_id` with an index; it runs on every status update."""
        await self._collection.create_index("order_id")

    async def get_by_order_id(self, order_id: str) -> DeliverySchema | None:
        return await self.find_one({"order_id": order_id})

    async def advance_status(self, delivery_id: str, new_status: DeliveryStatus) -> bool:
        """Move a delivery forward, or do nothing if the transition is illegal."""
        allowed = ALLOWED_PREVIOUS.get(new_status, set())
        if not allowed:
            return False

        result = await self._collection.update_one(
            {"_id": ObjectId(delivery_id), "status": {"$in": [status.value for status in allowed]}},
            {"$set": {"status": new_status.value}, "$inc": {"version": 1}},
        )
        return bool(result.modified_count)
