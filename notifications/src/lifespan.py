import logging

from fastapi import FastAPI

from src.common import setup_logging
from src.database import close_redis, setup_redis
from src.repositories import setup_repository
from src.services import setup_services
from src.streams import setup_streams, stop_streams


async def startup(app: FastAPI) -> None:
    """Startup sequence: Connect to Redis & initialize resources."""
    app.state.ready = False
    setup_logging()
    await setup_redis(app)
    await setup_repository(app)
    await setup_services(app)
    await setup_streams(app)

    app.state.ready = True
    logging.info("Notification service is ready.")


async def teardown(app: FastAPI) -> None:
    """Teardown sequence: Cancel subscriptions & close Redis connection."""
    app.state.ready = False
    await stop_streams(app)
    await close_redis(app)

    logging.info("Notification service shut down.")
