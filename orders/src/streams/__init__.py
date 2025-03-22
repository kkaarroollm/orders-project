import asyncio
import socket
import uuid

from fastapi import FastAPI

from src.config import settings
from src.streams.redis_stream_consumer import RedisStreamConsumer
from src.streams.redis_stream_publisher import RedisStreamPublisher


async def setup_streams(app: FastAPI) -> None:
    redis = app.state.redis_client
    service = app.state.order_service
    hostname = socket.gethostname()
    short_id = uuid.uuid4().hex[:6]

    stream = RedisStreamConsumer(
        redis=redis,
        stream=settings.order_status_stream,
        group=settings.orders_group,
        consumer_name=f"order-{hostname}-{short_id}",
    )

    app.state.subscription_task = asyncio.create_task(stream.listen(service.handle_status_update))


async def stop_streams(app: FastAPI) -> None:
    task = getattr(app.state, "subscription_task", None)
    if task and not task.done():
        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=5)
        except asyncio.CancelledError:
            pass


__all__ = ["RedisStreamConsumer", "RedisStreamPublisher", "setup_streams", "stop_streams"]
