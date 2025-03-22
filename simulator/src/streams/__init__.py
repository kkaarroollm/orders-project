import asyncio
import logging
import socket
import uuid

from redis.asyncio import Redis

from src.config import settings
from src.schemas import SimulationStream
from src.streams.redis_stream_consumer import RedisStreamConsumer
from src.streams.redis_stream_publisher import RedisStreamPublisher
from src.utils import handle_simulation_event


async def start_streams(redis: Redis) -> None:
    hostname = socket.gethostname()
    short_id = uuid.uuid4().hex[:6]
    consumer_name = f"simulator-{hostname}-{short_id}"

    order_consumer = RedisStreamConsumer(
        redis=redis, stream=settings.simulate_order_stream, group=settings.simulator_group, consumer_name=consumer_name
    )
    delivery_consumer = RedisStreamConsumer(
        redis=redis,
        stream=settings.simulate_delivery_stream,
        group=settings.simulator_group,
        consumer_name=consumer_name,
    )

    order_task = asyncio.create_task(
        order_consumer.listen(lambda payload: handle_simulation_event(SimulationStream.ORDER, payload, redis))
    )

    delivery_task = asyncio.create_task(
        delivery_consumer.listen(lambda payload: handle_simulation_event(SimulationStream.DELIVERY, payload, redis))
    )

    logging.info("🚀 Simulation workers started for ORDER and DELIVERY streams")
    await asyncio.gather(order_task, delivery_task)


__all__ = ["start_streams", "RedisStreamPublisher", "RedisStreamConsumer"]
