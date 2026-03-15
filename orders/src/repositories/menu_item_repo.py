from bson import ObjectId
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.collection import AsyncCollection
from shared.db.repository import MongoRepository

from src.schemas import MenuItemSchema


class MenuItemRepository(MongoRepository[MenuItemSchema]):
    def __init__(self, collection: AsyncCollection) -> None:
        super().__init__(collection, MenuItemSchema)

    async def decrement_stock(
        self, item_id: str, quantity: int, session: AsyncClientSession
    ) -> bool:
        return await self.update_one_by_filter(
            {"_id": ObjectId(item_id), "stock": {"$gte": quantity}},
            {"$inc": {"stock": -quantity}},
            session=session,
        )

    async def increment_stock(
        self, item_id: str, quantity: int, session: AsyncClientSession
    ) -> bool:
        return await self.update_one(
            item_id,
            {"$inc": {"stock": quantity}},
            session=session,
        )
