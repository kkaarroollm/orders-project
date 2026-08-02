import logging
from decimal import Decimal
from typing import Any

from pymongo import AsyncMongoClient
from shared.events.order import (
    OrderCreated,
    OrderSimulationRequested,
    OrderStatusChanged,
    OrderStatusSimulated,
)
from shared.redis.publisher import StreamProducer

from src.repositories.menu_item_repo import MenuItemRepository
from src.repositories.order_repository import OrderRepository
from src.responses import OrderResponse
from src.schemas import OrderSchema, OrderStatus
from src.services.mixins import TransactionServiceMixin


class OrderRejectedError(Exception):
    """Raised inside an order transaction so it aborts instead of committing.

    Returning from inside `async with self.transaction()` is a *normal* context
    exit, which commits -- leaving the stock already decremented for earlier
    items while no order was created.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


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
        try:
            async with self.transaction() as session:
                total_price = Decimal("0.00")

                for item in order_data.items:
                    menu_item = await self._menu_repo.get_by_id(item.item_id, session=None)
                    if not menu_item:
                        raise OrderRejectedError(f"Item with id={item.item_id} not found")

                    success = await self._menu_repo.decrement_stock(item.item_id, item.quantity, session)
                    if not success:
                        raise OrderRejectedError(f"Not enough stock for item_id={item.item_id}")

                    total_price += Decimal(str(menu_item.price)) * item.quantity

                order_data.total_price = total_price
                order_id_str = await self._order_repo.create(order_data, session)
                order_data.id = order_id_str
        except OrderRejectedError as rejected:
            logging.info("Rejected order: %s", rejected.message)
            return OrderResponse(order=order_data, success=False, message=rejected.message)

        await self._publisher.publish(
            OrderCreated(id=order_id_str, status=order_data.status.value, simulation=order_data.simulation),
            correlation_id=order_id_str,
        )

        if order_data.simulation != -1:
            await self._publisher.publish(
                OrderSimulationRequested(id=order_id_str),
                correlation_id=order_id_str,
            )
            logging.info("Simulating order %s", order_id_str)

        return OrderResponse(order=order_data, success=True)

    async def update_order_status(self, order_id: str, new_status: OrderStatus) -> OrderResponse:
        async with self.transaction() as session:
            updated = await self._order_repo.update_status(order_id, new_status, session)

        if updated:
            await self._publisher.publish(
                OrderStatusChanged(id=order_id, status=new_status.value),
                correlation_id=order_id,
            )
            return OrderResponse(order=None, success=True, message=f"Order {order_id} updated to {new_status}")

        return OrderResponse(order=None, success=False, message="Order not found or update failed")

    async def handle_status_update(self, event: OrderStatusSimulated) -> None:
        status = OrderStatus(event.status)
        logging.info("Order %s updated to %s", event.id, status)
        await self.update_order_status(event.id, status)
