import asyncio
import json
import logging
from decimal import Decimal

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorClientSession, AsyncIOMotorCollection
from redis.asyncio import Redis

from src.repositories.menu_item_repo import MenuItemRepository
from src.responses import OrderResponse
from src.schemas import OrderSchema, OrderStatus
from src.utils import with_mongodb_transaction
from bson import ObjectId


class OrderRepository:
    def __init__(self, collection: AsyncIOMotorCollection, mongo_client: AsyncIOMotorClient, redis_client: Redis):
        self._client = mongo_client
        self._collection = collection
        self._redis = redis_client
        self._active_tasks: set[asyncio.Task] = set()

    @property
    def active_tasks(self) -> set[asyncio.Task]:
        return self._active_tasks

    async def create_order(self, order_data: OrderSchema, session: AsyncIOMotorClientSession = None) -> str:
        doc = order_data.model_dump(by_alias=True, exclude={"id"})
        result = await self._collection.insert_one(doc, session=session)
        return str(result.inserted_id)

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
        simulator_task = asyncio.create_task(self._simulate_order(order_data.id))
        self._active_tasks.add(simulator_task)
        return OrderResponse(order=order_data, success=True)

    async def update_order_status(self, order_id: str, new_status: OrderStatus) -> bool:
        result = await self._collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": new_status.value}}
        )
        return result.modified_count > 0


    async def _simulate_order(self, order_id: str):
        """Method to simulate the ordering process."""
        try:
            await asyncio.sleep(20)
            await self.update_and_publish_order_status(order_id=order_id, new_status=OrderStatus.PREPARING)
            await asyncio.sleep(120)
            await self.update_and_publish_order_status(order_id=order_id, new_status=OrderStatus.OUT_FOR_DELIVERY)
        finally:
            self._active_tasks.discard(asyncio.current_task())

    async def update_and_publish_order_status(self, *, order_id: str, new_status: OrderStatus) -> bool:
        updated = await self.update_order_status(order_id, new_status)
        if not updated:
            return False
        if order := await self._collection.find_one({"_id": ObjectId(order_id)}):
            await self.publish_order_status(OrderSchema(**order))
        return updated

    async def publish_order_status(self, order_data: OrderSchema) -> None:
        data = json.dumps(order_data.model_dump(mode="json"))
        logging.info(f"📡 Publishing order: {data}")
        await self._redis.publish("orders_channel", data)
