import logging

from fastapi import FastAPI
from shared.logging import setup_logging
from shared.redis.connection import connect_redis

from src.repository import NotificationRepository
from src.service import NotificationService
from src.settings import settings
from src.state import AppState
from src.streams import setup_streams, stop_streams
from src.websockets import ws_order_status_manager


async def startup(app: FastAPI) -> None:
    setup_logging()
    redis_client = await connect_redis(settings.redis_url)

    notification_repo = NotificationRepository(redis_client)

    state = AppState(
        redis_client=redis_client,
        notification_repository=notification_repo,
        notification_service=NotificationService(notification_repo, ws_order_status_manager),
    )

    await setup_streams(state)
    state.ready = True
    app.state.ctx = state
    logging.info("Notification service is ready.")


async def teardown(app: FastAPI) -> None:
    state: AppState | None = getattr(app.state, "ctx", None)
    if not state:
        return
    state.ready = False
    await stop_streams(state)
    if state.redis_client:
        await state.redis_client.close()
    logging.info("Notification service shut down.")
