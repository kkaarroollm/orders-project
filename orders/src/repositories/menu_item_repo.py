import logging

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from redis.asyncio import Redis

from src.schemas import MenuItemSchema


class MenuItemRepository:
    def __init__(self, collection: AsyncIOMotorCollection, redis_client: Redis):
        self._collection = collection
        self._redis = redis_client

    async def get_menu_item(self, item_id: str) -> MenuItemSchema | None:
        if doc := await self._collection.find_one({"_id": ObjectId(item_id)}):
            return MenuItemSchema(**doc)
        return None

    async def get_all_menu_items(self) -> list[MenuItemSchema]:
        docs = await self._collection.find({}).to_list(length=1000)
        return [MenuItemSchema(**doc) for doc in docs]

    async def create_menu_item(self, item_data: MenuItemSchema) -> str:
        doc = item_data.model_dump(by_alias=True, exclude={"id"})
        result = await self._collection.insert_one(doc)
        return str(result.inserted_id)

    async def check_and_decrement_stock(self, item_id: str, quantity: int) -> bool:
        item_id_obj = ObjectId(item_id)
        doc = await self._collection.find_one({"_id": item_id_obj})
        if not doc:
            logging.error(f"❌ Item {item_id} not found in database.")
            return False

        current_stock = doc.get("stock", 0)
        logging.info(f"📦 Item {item_id} current stock: {current_stock}, requested: {quantity}")

        if current_stock < quantity:
            logging.error(f"❌ Not enough stock for item_id={item_id}")
            return False

        result = await self._collection.update_one(
            {"_id": item_id_obj, "stock": {"$gte": quantity}}, {"$inc": {"stock": -quantity}}
        )

        if result.modified_count == 0:
            logging.error(f"❌ Stock update failed for item_id={item_id}")
            return False

        logging.info(f"✅ Stock decremented for item_id={item_id}, remaining stock: {current_stock - quantity}")
        return result.modified_count > 0

    async def increment_stock(self, item_id: str, quantity: int) -> bool:
        result = await self._collection.update_one({"_id": item_id}, {"$inc": {"stock": quantity}})
        return result.modified_count > 0
