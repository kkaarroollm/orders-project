import logging
from typing import Any

from fastapi import FastAPI
from shared.logging import setup_logging
from shared.redis.publisher import StreamProducer

from src.databases import close_databases, setup_databases
from src.repositories.menu_item_repo import MenuItemRepository
from src.repositories.order_repository import OrderRepository
from src.services.menu_service import MenuService
from src.services.order_service import OrderService
from src.settings import settings
from src.streams import setup_streams, stop_streams


async def startup(app: FastAPI) -> None:
    app.state.ready = False
    setup_logging()
    await setup_databases(app)

    app.state.menu_repository = MenuItemRepository(
        collection=app.state.database.get_collection(settings.mongo_collection_menu_items),
    )
    app.state.order_repository = OrderRepository(
        collection=app.state.database.get_collection(settings.mongo_collection_orders),
    )

    publisher: StreamProducer[Any] = StreamProducer(app.state.redis_client, source="orders-service")
    app.state.menu_service = MenuService(repo=app.state.menu_repository, mongo_client=app.state.mongo_client)
    app.state.order_service = OrderService(
        order_repo=app.state.order_repository,
        menu_repo=app.state.menu_repository,
        publisher=publisher,
        mongo_client=app.state.mongo_client,
    )

    await setup_streams(app)
    app.state.ready = True
    logging.info("Orders service is ready.")


async def teardown(app: FastAPI) -> None:
    app.state.ready = False
    await stop_streams(app)
    await close_databases(app)
    logging.info("Orders service is shut down.")
