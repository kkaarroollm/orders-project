from pymongo import AsyncMongoClient

from src.repositories.menu_item_repo import MenuItemRepository
from src.schemas import MenuItemSchema
from src.services.mixins import TransactionServiceMixin


class MenuService(TransactionServiceMixin):
    def __init__(self, repo: MenuItemRepository, mongo_client: AsyncMongoClient) -> None:
        super().__init__(mongo_client)
        self._repo = repo

    async def get_item(self, item_id: str) -> MenuItemSchema | None:
        return await self._repo.get_by_id(item_id, session=None)

    async def list_items(self) -> list[MenuItemSchema]:
        return await self._repo.find_many({}, session=None)

    async def create_item(self, item: MenuItemSchema) -> str:
        async with self.transaction() as session:
            return await self._repo.create(item, session=session)
