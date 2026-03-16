from fastapi import FastAPI
from pydantic import BaseModel
from shared.redis.event_bus import EventBus

from src.settings import settings


class EventMessage(BaseModel):
    id: str | None = None
    order_id: str | None = None
    status: str | None = None


async def setup_streams(app: FastAPI) -> None:
    service = app.state.notification_service
    bus = EventBus(app.state.redis_client, group=settings.notifications_group)
    bus.subscribe(settings.orders_stream, EventMessage, service.handle_event)
    bus.subscribe(settings.deliveries_stream, EventMessage, service.handle_event)
    await bus.start()
    app.state.event_bus = bus


async def stop_streams(app: FastAPI) -> None:
    if bus := getattr(app.state, "event_bus", None):
        await bus.stop()
