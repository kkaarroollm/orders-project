from abc import ABC, abstractmethod
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClientSession

from src.schemas import MenuItemSchema


class IMenuItemRepository(ABC):
    """Interface for the MenuItem repository."""

    @abstractmethod
    async def get_menu_item(
        self, item_id: str, session: AsyncIOMotorClientSession | None
    ) -> Optional[MenuItemSchema]: ...

    @abstractmethod
    async def get_all_menu_items(self, session: AsyncIOMotorClientSession | None) -> list[MenuItemSchema]: ...

    @abstractmethod
    async def create_menu_item(self, item_data: MenuItemSchema, session: AsyncIOMotorClientSession) -> str: ...

    @abstractmethod
    async def decrement_stock(self, item_id: str, quantity: int, session: AsyncIOMotorClientSession) -> bool: ...

    @abstractmethod
    async def increment_stock(self, item_id: str, quantity: int, session: AsyncIOMotorClientSession) -> bool: ...
