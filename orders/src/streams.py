import asyncio
import socket
import uuid

from fastapi import FastAPI
from pydantic import BaseModel
from shared.redis.consumer import StreamConsumer

from src.config import settings


class StatusUpdateMessage(BaseModel):
    id: str
    status: str


async def setup_streams(app: FastAPI) -> None:
    redis = app.state.redis_client
    service = app.state.order_service
    hostname = socket.gethostname()
    short_id = uuid.uuid4().hex[:6]

    consumer: StreamConsumer[StatusUpdateMessage] = StreamConsumer(
        redis=redis,
        stream=settings.order_status_stream,
        group=settings.orders_group,
        consumer_name=f"order-{hostname}-{short_id}",
        message_type=StatusUpdateMessage,
    )

    async def handle_status_update(msg: StatusUpdateMessage) -> None:
        await service.handle_status_update({"id": msg.id, "status": msg.status})

    app.state.subscription_task = asyncio.create_task(consumer.listen(handle_status_update))


async def stop_streams(app: FastAPI) -> None:
    task = getattr(app.state, "subscription_task", None)
    if task and not task.done():
        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=5)
        except asyncio.CancelledError:
            pass
