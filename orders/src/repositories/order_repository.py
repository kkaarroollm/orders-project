import json
import logging
from decimal import Decimal

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorClientSession, AsyncIOMotorCollection
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

    async def create_order(self, order_data: OrderSchema, session: AsyncIOMotorClientSession = None) -> str:
        doc = order_data.model_dump(by_alias=True, exclude={"id"})
        result = await self._collection.insert_one(doc, session=session)
        return str(result.inserted_id)

    @with_mongodb_transaction(lambda self, *args, **kwargs: self._client)
    async def create_order_with_stock_check(
            self, order_data: OrderSchema, menu_repo: MenuItemRepository, session: AsyncIOMotorClientSession
    ) -> OrderResponse:
        total_price: Decimal = Decimal(0)

        for ordered_item in order_data.items:
            menu_item = await menu_repo.get_menu_item(ordered_item.item_id, session=session)

            if not menu_item:
                return OrderResponse(
                    order=order_data, success=False, message=f"Item with id={ordered_item.item_id} not found"
                )

            success = await menu_repo.decrement_stock(ordered_item.item_id, ordered_item.quantity, session=session)
            if not success:
                return OrderResponse(
                    order=order_data, success=False, message=f"Not enough stock for item_id={ordered_item.item_id}"
                )

            total_price += Decimal(menu_item.price) * ordered_item.quantity

        order_data.total_price = total_price
        doc = order_data.model_dump(by_alias=True, exclude={"id"}, mode="json")
        result = await self._collection.insert_one(doc, session=session)
        order_data.id = str(result.inserted_id)
        logging.info(f"📦 Order created: {order_data}")
        await self.publish_order_created(order_data)
        return OrderResponse(order=order_data, success=True)

    async def get_order(self, order_id: str, session: AsyncIOMotorClientSession = None) -> OrderSchema | None:
        if doc := await self._collection.find_one({"_id": order_id}, session=session):
            return OrderSchema(**doc)
        return None

    async def get_all_orders(self, session: AsyncIOMotorClientSession = None) -> list[OrderSchema]:
        docs = await self._collection.find({}, session=session).to_list(length=1000)
        return [OrderSchema(**d) for d in docs]

    async def publish_order_created(self, order_data: OrderSchema) -> None:
        data = json.dumps(order_data.model_dump(by_alias=True, mode="json"))
        logging.info(f"📡 Publishing order: {data}")
        await self._redis.publish("orders_channel", data)
