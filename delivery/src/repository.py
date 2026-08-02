from pymongo.asynchronous.collection import AsyncCollection
from shared.db.repository import MongoRepository

from src.schemas import DeliverySchema, DeliveryStatus


class DeliveryRepository(MongoRepository[DeliverySchema]):
    def __init__(self, collection: AsyncCollection) -> None:
        super().__init__(collection, DeliverySchema)

    async def ensure_indexes(self) -> None:
        """Back `get_by_order_id` with an index; it runs on every status update."""
        await self._collection.create_index("order_id")

    async def get_by_order_id(self, order_id: str) -> DeliverySchema | None:
        return await self.find_one({"order_id": order_id})

    async def update_status(self, delivery_id: str, new_status: DeliveryStatus) -> bool:
        return await self.update_one(
            delivery_id,
            {"$set": {"status": new_status.value}},
        )
