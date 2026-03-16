from fastapi import FastAPI
from pydantic import BaseModel
from shared.redis.event_bus import EventBus

from src.settings import settings


class StatusUpdateMessage(BaseModel):
    id: str
    status: str


async def setup_streams(app: FastAPI) -> None:
    bus = EventBus(app.state.redis_client, group=settings.orders_group)
    bus.subscribe(settings.order_status_stream, StatusUpdateMessage, app.state.order_service.handle_status_update)
    await bus.start()
    app.state.event_bus = bus


async def stop_streams(app: FastAPI) -> None:
    if bus := getattr(app.state, "event_bus", None):
        await bus.stop()
