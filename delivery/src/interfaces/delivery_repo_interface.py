from abc import ABC, abstractmethod
from typing import Optional

from src.schemas import DeliverySchema, DeliveryStatus


class IDeliveryRepository(ABC):
    """Interface class for MongoDB delivery repository"""

    @abstractmethod
    async def create(self, delivery: DeliverySchema) -> str:
        """Create a new delivery document in the database"""
        ...

    @abstractmethod
    async def get_by_order_id(self, order_id: str) ->Optional[DeliverySchema]:
        """Get delivery document by order_id"""
        ...

    @abstractmethod
    async def update_status(self, delivery_id: str, status: DeliveryStatus) -> bool:
        """Update delivery status by delivery_id"""
        ...
