import asyncio
import os
import socket
import uuid
from typing import Awaitable

from fastapi import FastAPI

from src.config import settings
from src.interfaces import INotificationService
from src.streams.redis_stream_consumer import RedisStreamConsumer


async def setup_streams(app: FastAPI) -> None:
    hostname = socket.gethostname()
    short_id = uuid.uuid4().hex[:6]

    service: INotificationService = app.state.notification_service
    redis = app.state.redis_client

    orders_consumer = RedisStreamConsumer(
        redis=redis,
        stream=settings.orders_stream,
        group=settings.notifications_group,
        consumer_name=f"notifications-{hostname}-{short_id}",
    )

    deliveries_consumer = RedisStreamConsumer(
        redis=redis,
        stream=settings.deliveries_stream,
        group=settings.notifications_group,
        consumer_name=f"notifications-{hostname}-{short_id}",
    )

    app.state.subscription_task = asyncio.create_task(
        _run_streams(orders_consumer.listen(service.handle_event), deliveries_consumer.listen(service.handle_event))
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
