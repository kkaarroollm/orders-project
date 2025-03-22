import logging
from decimal import Decimal
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient

from src.config import settings
from src.interfaces import IMenuItemRepository, IOrderRepository, IOrderService, IRedisStreamPublisher
from src.responses import OrderResponse
from src.schemas import OrderSchema, OrderStatus
from src.services.mixins import TransactionServiceMixin


class OrderService(TransactionServiceMixin, IOrderService):
    def __init__(
        self,
        order_repo: IOrderRepository,
        menu_repo: IMenuItemRepository,
        publisher: IRedisStreamPublisher,
        mongo_client: AsyncIOMotorClient,
    ):
        super().__init__(mongo_client)
        self._order_repo = order_repo
        self._menu_repo = menu_repo
        self._publisher = publisher

    async def get(self, order_id: str) -> Optional[OrderSchema]:
        return await self._order_repo.get(order_id, session=None)

    async def create_order_with_stock_check(self, order_data: OrderSchema) -> OrderResponse:
        async with self.transaction() as session:
            total_price = Decimal("0.00")

            for item in order_data.items:
                menu_item = await self._menu_repo.get_menu_item(item.item_id, session=None)
                if not menu_item:
                    return OrderResponse(
                        order=order_data, success=False, message=f"Item with id={item.item_id} not found"
                    )

                success = await self._menu_repo.decrement_stock(item.item_id, item.quantity, session)
                if not success:
                    return OrderResponse(
                        order=order_data, success=False, message=f"Not enough stock for item_id={item.item_id}"
                    )

                total_price += Decimal(menu_item.price) * item.quantity

            order_data.total_price = total_price
            order_id = await self._order_repo.create(order_data, session)
            order_data.id = order_id

        await self._publisher.publish(settings.orders_stream, order_data.model_dump(mode="json"))

        if order_data.simulation != -1:
            await self._publisher.publish(settings.simulate_order_stream, order_data.model_dump(mode="json"))
            logging.info(f"Simulating order {order_id}")

        return OrderResponse(order=order_data, success=True)

    async def update_order_status(self, order_id: str, new_status: OrderStatus) -> OrderResponse:
        async with self.transaction() as session:
            updated = await self._order_repo.update_status(order_id, new_status, session)

        if updated:
            await self._publisher.publish(settings.orders_stream, {"id": order_id, "status": new_status.value})
            return OrderResponse(order=None, success=True, message=f"Order {order_id} updated to {new_status}")

        return OrderResponse(order=None, success=False, message="Order not found or update failed")

    async def handle_status_update(self, data: dict) -> None:
        order_id = data["id"]
        status = OrderStatus(data["status"])
        logging.info(f"Order {order_id} updated to {status}")
        await self.update_order_status(order_id, status)
