from fastapi import FastAPI

from src.services.menu_service import MenuService
from src.services.mixins import TransactionServiceMixin
from src.services.order_service import OrderService
from src.streams import RedisStreamPublisher


async def setup_services(app: FastAPI) -> None:
    """Initialize all services with required dependencies and attach to app state."""
    publisher = RedisStreamPublisher(app.state.redis_client)
    menu_repo = app.state.menu_repository
    order_repo = app.state.order_repository

    app.state.menu_service = MenuService(repo=menu_repo, mongo_client=app.state.mongo_client)
    app.state.order_service = OrderService(
        order_repo=order_repo, menu_repo=menu_repo, publisher=publisher, mongo_client=app.state.mongo_client
    )


__all__ = [
    "MenuService",
    "OrderService",
    "TransactionServiceMixin",
    "setup_services",
]
