from abc import ABC, abstractmethod
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClientSession

from src.schemas import OrderSchema, OrderStatus


class IOrderRepository(ABC):
    """Interface for the Order repository."""

    @abstractmethod
    async def create(self, order_data: OrderSchema, session: AsyncIOMotorClientSession) -> str: ...

    @abstractmethod
    async def get(self, order_id: str, session: AsyncIOMotorClientSession | None) -> Optional[OrderSchema]: ...

    @abstractmethod
    async def update_status(
        self, order_id: str, new_status: OrderStatus, session: AsyncIOMotorClientSession
    ) -> bool: ...
