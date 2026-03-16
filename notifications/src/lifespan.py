import logging

from fastapi import FastAPI
from shared.logging import setup_logging
from shared.redis.connection import connect_redis

from src.repository import NotificationRepository
from src.service import NotificationService
from src.settings import settings
from src.streams import setup_streams, stop_streams
from src.websockets import ws_order_status_manager


async def startup(app: FastAPI) -> None:
    app.state.ready = False
    setup_logging()

    app.state.redis_client = await connect_redis(settings.redis_url)

    app.state.notification_repository = NotificationRepository(app.state.redis_client)
    app.state.notification_service = NotificationService(app.state.notification_repository, ws_order_status_manager)

    await setup_streams(app)
    app.state.ready = True
    logging.info("Notification service is ready.")


async def teardown(app: FastAPI) -> None:
    app.state.ready = False
    await stop_streams(app)
    if redis := getattr(app.state, "redis_client", None):
        await redis.close()
    logging.info("Notification service shut down.")
