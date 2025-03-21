import asyncio
import json
import logging
from decimal import Decimal
from typing import AsyncGenerator

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorClientSession, AsyncIOMotorCollection
from redis.asyncio import Redis

from src.repositories.menu_item_repo import MenuItemRepository
from src.responses import OrderResponse
from src.schemas import OrderSchema, OrderStatus
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

    async def get_order(self, order_id: str, session: AsyncIOMotorClientSession = None) -> OrderSchema | None:
        if doc := await self._collection.find_one({"_id": ObjectId(order_id)}, session=session):
            return OrderSchema(**doc)
        return None

    async def get_all_orders(self, session: AsyncIOMotorClientSession = None) -> list[OrderSchema]:
        docs = await self._collection.find({}, session=session).to_list(length=1000)
        return [OrderSchema(**d) for d in docs]

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
        await self.publish_order_status(order_data)
        if order_data.simulation != -1:
            await self.trigger_order_simulation(order_data.model_dump(mode="json"))
        return OrderResponse(order=order_data, success=True)

    async def trigger_order_simulation(self, order_data: dict) -> None:
        event = json.dumps(order_data)
        await self._redis.xadd("simulate_order_stream", {"data": event})

    async def update_order_status(self, order_id: str, new_status: OrderStatus) -> bool:
        result = await self._collection.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": new_status.value}})
        return bool(result.modified_count)

    async def update_and_publish_order_status(self, *, order_id: str, new_status: OrderStatus) -> bool:
        updated = await self.update_order_status(order_id, new_status)
        if not updated:
            raise ValueError(f"Can't update order status for order_id={order_id}")
        if order := await self._collection.find_one({"_id": ObjectId(order_id)}):
            await self.publish_order_status(OrderSchema(**order))
        return updated

    async def publish_order_status(self, order_data: OrderSchema) -> None:
        data = json.dumps(order_data.model_dump(mode="json"))
        logging.info(f"📡 Publishing order status: {data}")
        await self._redis.xadd("orders_stream", {"data": data})

    async def get_last_stream_id(self, stream_name: str) -> str:
        return await self._redis.get(f"last_id:{stream_name}") or "0-0"

    async def read_stream(self, stream_name: str) -> AsyncGenerator[tuple[str, dict], None]:
        last_id = await self.get_last_stream_id(stream_name)

        while True:
            try:
                if not (streams := await self._redis.xread({stream_name: last_id}, block=5000, count=10)):
                    await asyncio.sleep(1)
                    continue

                for last_id, message_data in (msg for _, msgs in streams for msg in msgs):
                    yield last_id, message_data
                    await self._redis.set(f"last_id:{stream_name}", last_id)

            except Exception as e:
                logging.error(f"Error reading Redis stream {stream_name}: {e}")
                await asyncio.sleep(1)

    async def subscribe_to_status_changes(self) -> None:
        async for message_id, message in self.read_stream("order_status_stream"):
            try:
                message_data = json.loads(message["data"])
                await self.update_and_publish_order_status(
                    order_id=message_data.get("id"), new_status=OrderStatus(message_data["status"])
                )
            except Exception as e:
                logging.error(f"Error while processing message from `order_status_stream`: {message}, error: {e}")
                continue
