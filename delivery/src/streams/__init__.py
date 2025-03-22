import asyncio
import socket
import uuid
from collections.abc import Awaitable

from fastapi import FastAPI

from src.config import settings
from src.interfaces import IDeliveryService
from src.streams.redis_stream_consumer import RedisStreamConsumer
from src.streams.redis_stream_publisher import RedisStreamPublisher


async def setup_streams(app: FastAPI) -> None:
    service: IDeliveryService = app.state.delivery_service
    redis = app.state.redis_client
    hostname = socket.gethostname()
    short_id = uuid.uuid4().hex[:6]

    orders = RedisStreamConsumer(
        redis=redis,
        stream=settings.orders_stream,
        group=settings.delivery_group,
        consumer_name=f"delivery-{hostname}-{short_id}",
    )
    status = RedisStreamConsumer(
        redis=redis,
        stream=settings.delivery_status_stream,
        group=settings.delivery_group,
        consumer_name=f"delivery-{hostname}-{short_id}",
    )

    app.state.subscription_task = asyncio.create_task(
        _run_streams(orders.listen(service.handle_order), status.listen(service.handle_status_update))
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


__all__ = ["RedisStreamConsumer", "RedisStreamPublisher", "setup_streams", "stop_streams"]
