import asyncio
import logging
import socket
import uuid
from typing import Any

from pydantic import BaseModel
from redis.asyncio import Redis
from shared.redis.consumer import StreamConsumer
from shared.redis.publisher import StreamProducer

from src.config import settings
from src.schemas import SimulationStream
from src.utils import handle_simulation_event


class SimulationEvent(BaseModel):
    id: str
    status: str | None = None


async def start_streams(redis: Redis) -> None:
    hostname = socket.gethostname()
    short_id = uuid.uuid4().hex[:6]
    consumer_name = f"simulator-{hostname}-{short_id}"

    producer: StreamProducer[Any] = StreamProducer(redis)

    order_consumer: StreamConsumer[SimulationEvent] = StreamConsumer(
        redis=redis,
        stream=settings.simulate_order_stream,
        group=settings.simulator_group,
        consumer_name=consumer_name,
        message_type=SimulationEvent,
    )
    delivery_consumer: StreamConsumer[SimulationEvent] = StreamConsumer(
        redis=redis,
        stream=settings.simulate_delivery_stream,
        group=settings.simulator_group,
        consumer_name=consumer_name,
        message_type=SimulationEvent,
    )

    async def handle_order(msg: SimulationEvent) -> None:
        await handle_simulation_event(SimulationStream.ORDER, msg.model_dump(), producer)

    async def handle_delivery(msg: SimulationEvent) -> None:
        await handle_simulation_event(SimulationStream.DELIVERY, msg.model_dump(), producer)

    order_task = asyncio.create_task(order_consumer.listen(handle_order))
    delivery_task = asyncio.create_task(delivery_consumer.listen(handle_delivery))

    logging.info("Simulation workers started for ORDER and DELIVERY streams")
    await asyncio.gather(order_task, delivery_task)
