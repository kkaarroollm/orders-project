import asyncio
import logging
from typing import Any

from fastapi import FastAPI
from shared.db.outbox import MongoOutbox, OutboxRelay
from shared.logging import setup_logging
from shared.redis.event_bus import terminate_on_failure
from shared.redis.publisher import StreamProducer

from src.databases import close_databases, connect_databases
from src.repositories.menu_item_repo import MenuItemRepository
from src.repositories.order_repository import OrderRepository
from src.services.menu_service import MenuService
from src.services.order_service import OrderService
from src.settings import settings
from src.state import AppState
from src.streams import setup_streams, stop_streams


def _on_relay_stopped(task: asyncio.Task[None]) -> None:
    """Same policy as a dead stream consumer.

    `run()` loops forever, so any completion means nothing is publishing --
    the pod still serves HTTP but no event ever leaves the outbox.
    """
    if task.cancelled():
        return  # expected during teardown
    terminate_on_failure("outbox-relay", task.exception() or RuntimeError("outbox relay exited"))


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

    outbox = MongoOutbox(collection=database.get_collection(settings.mongo_collection_outbox))
    await outbox.ensure_indexes()
    relay = OutboxRelay(outbox=outbox, producer=publisher)

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
            outbox=outbox,
            mongo_client=mongo_client,
        ),
        outbox_relay=relay,
    )

    relay.start().add_done_callback(_on_relay_stopped)

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
    if state.outbox_relay:
        await state.outbox_relay.stop()
    await close_databases(mongo_client=state.mongo_client, redis_client=state.redis_client)
    logging.info("Orders service is shut down.")
