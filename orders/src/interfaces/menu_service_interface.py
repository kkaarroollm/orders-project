from abc import ABC, abstractmethod
from typing import Optional

from src.schemas import MenuItemSchema


class IMenuService(ABC):
    @abstractmethod
    async def get_item(self, item_id: str) -> Optional[MenuItemSchema]: ...

    @abstractmethod
    async def list_items(self) -> list[MenuItemSchema]: ...

    @abstractmethod
    async def create_item(self, item: MenuItemSchema) -> str: ...
