import socket

from shared.events.delivery import DeliveryCreated, DeliveryStatusChanged
from shared.events.notifications import OrderStatusPush
from shared.events.order import OrderCreated, OrderStatusChanged
from shared.redis.event_bus import EventBus

from src.settings import settings
from src.state import AppState


async def setup_streams(state: AppState) -> None:
    service = state.notification_service

    # Shared group: each domain event is handled once across all replicas.
    bus = EventBus(state.redis_client, group=settings.notifications_group)
    bus.subscribe(OrderCreated, service.handle_order_event)
    bus.subscribe(OrderStatusChanged, service.handle_order_event)
    bus.subscribe(DeliveryCreated, service.handle_delivery_event)
    bus.subscribe(DeliveryStatusChanged, service.handle_delivery_event)
    await bus.start()
    state.event_bus = bus

    # Group per replica: every replica sees every push, and pushes it to
    # whichever clients it happens to be holding.
    fanout = EventBus(
        state.redis_client,
        group=f"{settings.fanout_group_prefix}-{socket.gethostname()}",
        fanout=True,
    )
    fanout.subscribe(OrderStatusPush, state.status_push_fanout.handle_push)
    await fanout.start()
    state.fanout_bus = fanout


async def stop_streams(state: AppState) -> None:
    if state.event_bus:
        await state.event_bus.stop()
    if state.fanout_bus:
        await state.fanout_bus.stop()
