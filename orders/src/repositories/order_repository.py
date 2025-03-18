import json
import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from redis.asyncio import Redis

from src.repositories.menu_item_repo import MenuItemRepository
from src.responses import OrderResponse
from src.schemas import OrderSchema
from src.utils import with_mongodb_transaction


class OrderRepository:
    def __init__(self, collection: AsyncIOMotorCollection, mongo_client: AsyncIOMotorClient, redis_client: Redis):
        self._client = mongo_client
        self._collection = collection
        self._redis = redis_client

    async def create_order(self, order_data: OrderSchema) -> str:
        doc = order_data.model_dump(by_alias=True, exclude={"id"})
        result = await self._collection.insert_one(doc)
        return str(result.inserted_id)

    @with_mongodb_transaction(lambda self, *args, **kwargs: self._client)
    async def create_order_with_stock_check(
        self, order_data: OrderSchema, menu_repo: MenuItemRepository
    ) -> OrderResponse:
        for ordered_item in order_data.items:
            success = await menu_repo.check_and_decrement_stock(ordered_item.item_id, ordered_item.quantity)
            if not success:
                return OrderResponse(
                    order=order_data, success=False, message=f"Not enough stock for item_id={ordered_item.item_id}"
                )

        doc = order_data.model_dump(by_alias=True, exclude={"id"}, mode="json")
        result = await self._collection.insert_one(doc)
        order_data.id = str(result.inserted_id)
        logging.info(f"📦 Order created: {order_data}")
        await self.publish_order_created(order_data)
        return OrderResponse(order=order_data, success=True)

    async def get_order(self, order_id: str) -> OrderSchema | None:
        if doc := await self._collection.find_one({"_id": order_id}):
            return OrderSchema(**doc)
        return None

    async def get_all_orders(self) -> list[OrderSchema]:
        docs = await self._collection.find().to_list(length=1000)
        return [OrderSchema(**d) for d in docs]

    async def publish_order_created(self, order_data: OrderSchema) -> None:
        data = json.dumps(order_data.model_dump(by_alias=True, mode="json"))
        logging.info(f"📡 Publishing order: {data}")
        await self._redis.publish("orders_channel", data)
