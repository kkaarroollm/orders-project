from abc import ABC, abstractmethod
from typing import Any


class INotificationRepository(ABC):
    @abstractmethod
    async def set_order_status(self, order_id: str, message: dict, expire: int = 86400) -> None: ...

    @abstractmethod
    async def get_order_status(self, order_id: str) -> dict[str, Any]: ...
