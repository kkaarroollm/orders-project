from pydantic import BaseModel
from shared.redis.event_bus import EventBus

from src.settings import settings
from src.state import AppState


class OrderEvent(BaseModel):
    id: str
    status: str
    simulation: int = 1


class DeliveryStatusEvent(BaseModel):
    id: str | None = None
    order_id: str | None = None
    status: str


async def setup_streams(state: AppState) -> None:
    bus = EventBus(state.redis_client, group=settings.delivery_group)
    bus.subscribe(settings.orders_stream, OrderEvent, state.delivery_service.handle_order)
    bus.subscribe(settings.delivery_status_stream, DeliveryStatusEvent, state.delivery_service.handle_status_update)
    await bus.start()
    state.event_bus = bus


async def stop_streams(state: AppState) -> None:
    if state.event_bus:
        await state.event_bus.stop()
