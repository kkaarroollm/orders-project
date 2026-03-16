from fastapi import FastAPI
from pydantic import BaseModel
from shared.redis.event_bus import EventBus

from src.settings import settings


class OrderEvent(BaseModel):
    id: str
    status: str
    simulation: int = 1


class DeliveryStatusEvent(BaseModel):
    id: str | None = None
    order_id: str | None = None
    status: str


async def setup_streams(app: FastAPI) -> None:
    service = app.state.delivery_service
    bus = EventBus(app.state.redis_client, group=settings.delivery_group)
    bus.subscribe(settings.orders_stream, OrderEvent, service.handle_order)
    bus.subscribe(settings.delivery_status_stream, DeliveryStatusEvent, service.handle_status_update)
    await bus.start()
    app.state.event_bus = bus


async def stop_streams(app: FastAPI) -> None:
    if bus := getattr(app.state, "event_bus", None):
        await bus.stop()
