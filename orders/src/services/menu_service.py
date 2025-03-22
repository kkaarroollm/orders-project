from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient

from src.interfaces import IMenuItemRepository, IMenuService
from src.schemas import MenuItemSchema
from src.services.mixins import TransactionServiceMixin


class MenuService(TransactionServiceMixin, IMenuService):
    def __init__(self, repo: IMenuItemRepository, mongo_client: AsyncIOMotorClient):
        super().__init__(mongo_client)
        self._repo = repo

    async def get_item(self, item_id: str) -> Optional[MenuItemSchema]:
        return await self._repo.get_menu_item(item_id, session=None)

    async def list_items(self) -> list[MenuItemSchema]:
        return await self._repo.get_all_menu_items(session=None)

    async def create_item(self, item: MenuItemSchema) -> str:
        async with self.transaction() as session:
            return await self._repo.create_menu_item(item, session=session)
