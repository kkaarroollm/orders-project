from pydantic import BaseModel
from shared.redis.event_bus import EventBus

from src.settings import settings
from src.state import AppState


class EventMessage(BaseModel):
    id: str | None = None
    order_id: str | None = None
    status: str | None = None


async def setup_streams(state: AppState) -> None:
    bus = EventBus(state.redis_client, group=settings.notifications_group)
    bus.subscribe(settings.orders_stream, EventMessage, state.notification_service.handle_event)
    bus.subscribe(settings.deliveries_stream, EventMessage, state.notification_service.handle_event)
    await bus.start()
    state.event_bus = bus


async def stop_streams(state: AppState) -> None:
    if state.event_bus:
        await state.event_bus.stop()
