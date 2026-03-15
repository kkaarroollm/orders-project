from fastapi import FastAPI

from src.config import settings
from src.repositories.menu_item_repo import MenuItemRepository
from src.repositories.order_repository import OrderRepository


async def setup_repositories(app: FastAPI) -> None:
    app.state.menu_repository = MenuItemRepository(
        collection=app.state.database.get_collection(settings.mongo_collection_menu_items),
    )
    app.state.order_repository = OrderRepository(
        collection=app.state.database.get_collection(settings.mongo_collection_orders),
    )


__all__ = ["MenuItemRepository", "OrderRepository", "setup_repositories"]
