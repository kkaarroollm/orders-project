import logging
from typing import Any

from fastapi import FastAPI
from shared.logging import setup_logging
from shared.redis.publisher import StreamProducer

from src.databases import close_databases, connect_databases
from src.repository import DeliveryRepository
from src.service import DeliveryService
from src.settings import settings
from src.state import AppState
from src.streams import setup_streams, stop_streams


async def startup(app: FastAPI) -> None:
    setup_logging()
    mongo_client, database, redis_client = await connect_databases()

    delivery_repo = DeliveryRepository(
        collection=database.get_collection(settings.mongo_collection_deliveries),
    )

    publisher: StreamProducer[Any] = StreamProducer(redis_client, source="delivery-service")

    state = AppState(
        mongo_client=mongo_client,
        database=database,
        redis_client=redis_client,
        delivery_repo=delivery_repo,
        delivery_service=DeliveryService(repo=delivery_repo, publisher=publisher),
    )

    await setup_streams(state)
    state.ready = True
    app.state.ctx = state
    logging.info("Delivery service is ready.")


async def teardown(app: FastAPI) -> None:
    state: AppState | None = getattr(app.state, "ctx", None)
    if not state:
        return
    state.ready = False
    await stop_streams(state)
    await close_databases(mongo_client=state.mongo_client, redis_client=state.redis_client)
    logging.info("Delivery service shut down.")
