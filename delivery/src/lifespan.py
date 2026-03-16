import logging
from typing import Any

from fastapi import FastAPI
from shared.logging import setup_logging
from shared.redis.publisher import StreamProducer

from src.databases import close_databases, setup_databases
from src.repository import DeliveryRepository
from src.service import DeliveryService
from src.settings import settings
from src.streams import setup_streams, stop_streams


async def startup(app: FastAPI) -> None:
    app.state.ready = False
    setup_logging()
    await setup_databases(app)

    app.state.delivery_repo = DeliveryRepository(
        collection=app.state.database.get_collection(settings.mongo_collection_deliveries),
    )

    publisher: StreamProducer[Any] = StreamProducer(app.state.redis_client, source="delivery-service")
    app.state.delivery_service = DeliveryService(repo=app.state.delivery_repo, publisher=publisher)

    await setup_streams(app)
    app.state.ready = True
    logging.info("Delivery service is ready.")


async def teardown(app: FastAPI) -> None:
    app.state.ready = False
    await stop_streams(app)
    await close_databases(app)
    logging.info("Delivery service shut down.")
