import logging
from typing import Any

from fastapi import FastAPI
from shared.logging import setup_logging
from shared.redis.publisher import StreamProducer

from src.databases import close_databases, connect_databases
from src.repositories.menu_item_repo import MenuItemRepository
from src.repositories.order_repository import OrderRepository
from src.services.menu_service import MenuService
from src.services.order_service import OrderService
from src.settings import settings
from src.state import AppState
from src.streams import setup_streams, stop_streams


async def startup(app: FastAPI) -> None:
    setup_logging()
    mongo_client, database, redis_client = await connect_databases()

    menu_repo = MenuItemRepository(
        collection=database.get_collection(settings.mongo_collection_menu_items),
    )
    order_repo = OrderRepository(
        collection=database.get_collection(settings.mongo_collection_orders),
    )

    publisher: StreamProducer[Any] = StreamProducer(redis_client, source="orders-service")

    state = AppState(
        mongo_client=mongo_client,
        database=database,
        redis_client=redis_client,
        menu_repository=menu_repo,
        order_repository=order_repo,
        menu_service=MenuService(repo=menu_repo, mongo_client=mongo_client),
        order_service=OrderService(
            order_repo=order_repo,
            menu_repo=menu_repo,
            publisher=publisher,
            mongo_client=mongo_client,
        ),
    )

    await setup_streams(state)
    state.ready = True
    app.state.ctx = state
    logging.info("Orders service is ready.")


async def teardown(app: FastAPI) -> None:
    state: AppState | None = getattr(app.state, "ctx", None)
    if not state:
        return
    state.ready = False
    await stop_streams(state)
    await close_databases(mongo_client=state.mongo_client, redis_client=state.redis_client)
    logging.info("Orders service is shut down.")
