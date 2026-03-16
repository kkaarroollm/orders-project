from typing import Any

from pydantic import BaseModel
from redis.asyncio import Redis
from shared.redis.event_bus import EventBus
from shared.redis.publisher import StreamProducer

from src.schemas import SimulationStream
from src.settings import settings
from src.utils import handle_simulation_event


class SimulationEvent(BaseModel):
    id: str
    status: str | None = None


async def start_streams(redis: Redis) -> None:
    producer: StreamProducer[Any] = StreamProducer(redis)

    async def handle_order(msg: SimulationEvent) -> None:
        await handle_simulation_event(SimulationStream.ORDER, msg.model_dump(), producer)

    async def handle_delivery(msg: SimulationEvent) -> None:
        await handle_simulation_event(SimulationStream.DELIVERY, msg.model_dump(), producer)

    bus = EventBus(redis, group=settings.simulator_group)
    bus.subscribe(settings.simulate_order_stream, SimulationEvent, handle_order)
    bus.subscribe(settings.simulate_delivery_stream, SimulationEvent, handle_delivery)
    await bus.run_forever()
