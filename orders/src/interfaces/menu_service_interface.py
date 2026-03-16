from typing import Protocol, runtime_checkable

from src.schemas import MenuItemSchema

__all__ = ["MenuServiceProtocol"]


@runtime_checkable
class MenuServiceProtocol(Protocol):
    async def get_item(self, item_id: str) -> MenuItemSchema | None: ...
    async def list_items(self) -> list[MenuItemSchema]: ...
    async def create_item(self, item: MenuItemSchema) -> str: ...

