from abc import ABC, abstractmethod
from typing import Optional

from src.responses import OrderResponse
from src.schemas import OrderSchema, OrderStatus


class IOrderService(ABC):
    @abstractmethod
    async def get(self, order_id: str) -> Optional[OrderSchema]: ...

    @abstractmethod
    async def create_order_with_stock_check(self, order_data: OrderSchema) -> OrderResponse: ...

    @abstractmethod
    async def update_order_status(self, order_id: str, new_status: OrderStatus) -> OrderResponse: ...
