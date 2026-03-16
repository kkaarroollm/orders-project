import asyncio
import socket
import uuid
from collections.abc import Awaitable

from fastapi import FastAPI
from pydantic import BaseModel
from shared.redis.consumer import StreamConsumer

from src.settings import settings


class EventMessage(BaseModel):
    id: str | None = None
    order_id: str | None = None
    status: str | None = None


async def setup_streams(app: FastAPI) -> None:
    hostname = socket.gethostname()
    short_id = uuid.uuid4().hex[:6]
    consumer_name = f"notifications-{hostname}-{short_id}"

    service = app.state.notification_service
    redis = app.state.redis_client

    orders_consumer: StreamConsumer[EventMessage] = StreamConsumer(
        redis=redis,
        stream=settings.orders_stream,
        group=settings.notifications_group,
        consumer_name=consumer_name,
        message_type=EventMessage,
    )

    deliveries_consumer: StreamConsumer[EventMessage] = StreamConsumer(
        redis=redis,
        stream=settings.deliveries_stream,
        group=settings.notifications_group,
        consumer_name=consumer_name,
        message_type=EventMessage,
    )

    async def handle_event(msg: EventMessage) -> None:
        await service.handle_event(msg.model_dump(exclude_none=True))

    app.state.subscription_task = asyncio.create_task(
        _run_streams(orders_consumer.listen(handle_event), deliveries_consumer.listen(handle_event))
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
