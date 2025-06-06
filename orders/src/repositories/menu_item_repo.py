from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClientSession, AsyncIOMotorCollection
from redis.asyncio import Redis

from src.interfaces import IMenuItemRepository
from src.schemas import MenuItemSchema


class MenuItemRepository(IMenuItemRepository):
    def __init__(self, collection: AsyncIOMotorCollection, redis_client: Redis):
        self._collection = collection
        self._redis = redis_client

    async def get_menu_item(self, item_id: str, session: AsyncIOMotorClientSession | None) -> MenuItemSchema | None:
        doc = await self._collection.find_one({"_id": ObjectId(item_id)}, session=session)
        return MenuItemSchema(**doc) if doc else None

    async def get_all_menu_items(self, session: AsyncIOMotorClientSession | None) -> list[MenuItemSchema]:
        docs = await self._collection.find({}, session=session).to_list(length=1000)
        return [MenuItemSchema(**doc) for doc in docs]

    async def create_menu_item(self, item_data: MenuItemSchema, session: AsyncIOMotorClientSession) -> str:
        doc = item_data.model_dump(by_alias=True, exclude={"id"})
        result = await self._collection.insert_one(doc, session=session)
        return str(result.inserted_id)

    async def decrement_stock(self, item_id: str, quantity: int, session: AsyncIOMotorClientSession) -> bool:
        result = await self._collection.update_one(
            {"_id": ObjectId(item_id), "stock": {"$gte": quantity}},
            {"$inc": {"stock": -quantity}},
            session=session,
        )
        return bool(result.modified_count)

    async def increment_stock(self, item_id: str, quantity: int, session: AsyncIOMotorClientSession) -> bool:
        result = await self._collection.update_one(
            {"_id": ObjectId(item_id)},
            {"$inc": {"stock": quantity}},
            session=session,
        )
        return bool(result.modified_count)
