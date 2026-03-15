from typing import Protocol, runtime_checkable

from src.responses import OrderResponse
from src.schemas import OrderSchema, OrderStatus

__all__ = ["OrderServiceProtocol"]


@runtime_checkable
class OrderServiceProtocol(Protocol):
    async def get(self, order_id: str) -> OrderSchema | None: ...
    async def create_order_with_stock_check(self, order_data: OrderSchema) -> OrderResponse: ...
    async def update_order_status(self, order_id: str, new_status: OrderStatus) -> OrderResponse: ...
