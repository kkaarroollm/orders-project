from abc import ABC, abstractmethod


class IDeliveryService(ABC):
    """Interface for handling delivery business logic service operations"""

    @abstractmethod
    async def handle_order(self, order_data: dict) -> None:
        """Process a new order and start delivery."""
        ...

    @abstractmethod
    async def handle_status_update(self, status_data: dict) -> None:
        """Update and publish delivery status."""
        ...
