import asyncio
import socket
import uuid
from collections.abc import Awaitable

from fastapi import FastAPI
from pydantic import BaseModel
from shared.redis.consumer import StreamConsumer

from src.config import settings


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
    redis = app.state.redis_client
    hostname = socket.gethostname()
    short_id = uuid.uuid4().hex[:6]
    consumer_name = f"delivery-{hostname}-{short_id}"

    orders_consumer: StreamConsumer[OrderEvent] = StreamConsumer(
        redis=redis,
        stream=settings.orders_stream,
        group=settings.delivery_group,
        consumer_name=consumer_name,
        message_type=OrderEvent,
    )
    status_consumer: StreamConsumer[DeliveryStatusEvent] = StreamConsumer(
        redis=redis,
        stream=settings.delivery_status_stream,
        group=settings.delivery_group,
        consumer_name=consumer_name,
        message_type=DeliveryStatusEvent,
    )

    async def handle_order(msg: OrderEvent) -> None:
        await service.handle_order(msg.model_dump())

    async def handle_status(msg: DeliveryStatusEvent) -> None:
        await service.handle_status_update(msg.model_dump())

    app.state.subscription_task = asyncio.create_task(
        _run_streams(orders_consumer.listen(handle_order), status_consumer.listen(handle_status))
    )


async def _run_streams(*streams: Awaitable[None]) -> None:
    await asyncio.gather(*streams)


async def stop_streams(app: FastAPI) -> None:
    task = getattr(app.state, "subscription_task", None)
    if task and not task.done():
        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=5)
        except asyncio.CancelledError:
            pass
