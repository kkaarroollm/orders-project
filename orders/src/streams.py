from shared.events.order import OrderStatusSimulated
from shared.redis.event_bus import EventBus

from src.settings import settings
from src.state import AppState


async def setup_streams(state: AppState) -> None:
    bus = EventBus(state.redis_client, group=settings.orders_group)
    bus.subscribe(OrderStatusSimulated, state.order_service.handle_status_update)
    await bus.start()
    state.event_bus = bus


async def stop_streams(state: AppState) -> None:
    if state.event_bus:
        await state.event_bus.stop()
