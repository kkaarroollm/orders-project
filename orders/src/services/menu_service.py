from pymongo import AsyncMongoClient

from src.cache import MenuCache
from src.repositories.menu_item_repo import MenuItemRepository
from src.schemas import MenuItemSchema
from src.services.mixins import TransactionServiceMixin


class MenuService(TransactionServiceMixin):
    def __init__(
        self,
        repo: MenuItemRepository,
        read_repo: MenuItemRepository,
        cache: MenuCache,
        mongo_client: AsyncMongoClient,
    ) -> None:
        super().__init__(mongo_client)
        self._repo = repo
        # Reads may go to a secondary; writes and transactions must not.
        self._read_repo = read_repo
        self._cache = cache

    async def get_item(self, item_id: str) -> MenuItemSchema | None:
        return await self._read_repo.get_by_id(item_id, session=None)

    async def list_items(self) -> list[MenuItemSchema]:
        if (cached := await self._cache.get()) is not None:
            return cached

        items = await self._read_repo.find_many({}, session=None)
        await self._cache.set(items)
        return items

    async def create_item(self, item: MenuItemSchema) -> str:
        async with self.transaction() as session:
            item_id = await self._repo.create(item, session=session)
        await self._cache.invalidate()
        return item_id
