import logging
from decimal import Decimal
from typing import Any

from pymongo import AsyncMongoClient
from shared.redis.publisher import StreamProducer

from src.repositories.menu_item_repo import MenuItemRepository
from src.repositories.order_repository import OrderRepository
from src.responses import OrderResponse
from src.schemas import OrderSchema, OrderStatus
from src.services.mixins import TransactionServiceMixin
from src.settings import settings


class OrderService(TransactionServiceMixin):
    def __init__(
        self,
        order_repo: OrderRepository,
        menu_repo: MenuItemRepository,
        publisher: StreamProducer[Any],
        mongo_client: AsyncMongoClient,
    ) -> None:
        super().__init__(mongo_client)
        self._order_repo = order_repo
        self._menu_repo = menu_repo
        self._publisher = publisher

    async def get(self, order_id: str) -> OrderSchema | None:
        return await self._order_repo.get_by_id(order_id, session=None)

    async def create_order_with_stock_check(self, order_data: OrderSchema) -> OrderResponse:
        async with self.transaction() as session:
            total_price = Decimal("0.00")

            for item in order_data.items:
                menu_item = await self._menu_repo.get_by_id(item.item_id, session=None)
                if not menu_item:
                    return OrderResponse(
                        order=order_data, success=False, message=f"Item with id={item.item_id} not found"
                    )

                success = await self._menu_repo.decrement_stock(item.item_id, item.quantity, session)
                if not success:
                    return OrderResponse(
                        order=order_data, success=False, message=f"Not enough stock for item_id={item.item_id}"
                    )

                total_price += Decimal(str(menu_item.price)) * item.quantity

            order_data.total_price = total_price
            order_id_str = await self._order_repo.create(order_data, session)
            order_data.id = order_id_str

        await self._publisher.publish_raw(settings.orders_stream, order_data.model_dump(mode="json"))

        if order_data.simulation != -1:
            await self._publisher.publish_raw(settings.simulate_order_stream, order_data.model_dump(mode="json"))
            logging.info("Simulating order %s", order_id_str)

        return OrderResponse(order=order_data, success=True)

    async def update_order_status(self, order_id: str, new_status: OrderStatus) -> OrderResponse:
        async with self.transaction() as session:
            updated = await self._order_repo.update_status(order_id, new_status, session)

        if updated:
            await self._publisher.publish_raw(settings.orders_stream, {"id": order_id, "status": new_status.value})
            return OrderResponse(order=None, success=True, message=f"Order {order_id} updated to {new_status}")

        return OrderResponse(order=None, success=False, message="Order not found or update failed")

    async def handle_status_update(self, data: dict[str, str]) -> None:
        order_id = data["id"]
        status = OrderStatus(data["status"])
        logging.info("Order %s updated to %s", order_id, status)
        await self.update_order_status(order_id, status)
