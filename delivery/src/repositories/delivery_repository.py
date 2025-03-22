from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from src.interfaces import IDeliveryRepository
from src.schemas import DeliverySchema, DeliveryStatus


class DeliveryRepository(IDeliveryRepository):
    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self._collection = collection

    async def create(self, delivery: DeliverySchema) -> str:
        doc = delivery.model_dump(by_alias=True, exclude={"id"})
        result = await self._collection.insert_one(doc)
        return str(result.inserted_id)

    async def get_by_order_id(self, order_id: str) -> Optional[DeliverySchema]:
        delivery = await self._collection.find_one({"order_id": order_id})
        return DeliverySchema(**delivery) if delivery else None

    async def update_status(self, delivery_id: str, new_status: DeliveryStatus) -> bool:
        result = await self._collection.update_one(
            {"_id": ObjectId(delivery_id)}, {"$set": {"status": new_status.value}}
        )
        return bool(result.modified_count)
