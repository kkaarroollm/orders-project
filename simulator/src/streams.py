from typing import Any

from redis.asyncio import Redis
from shared.events.delivery import DeliverySimulationRequested
from shared.events.order import OrderSimulationRequested
from shared.redis.event_bus import EventBus
from shared.redis.publisher import StreamProducer

from src.schemas import SimulationStream
from src.settings import settings
from src.utils import handle_simulation_event


async def start_streams(redis: Redis) -> None:
    producer: StreamProducer[Any] = StreamProducer(redis, source="simulator")

    async def handle_order(event: OrderSimulationRequested) -> None:
        await handle_simulation_event(SimulationStream.ORDER, event.id, producer)

    async def handle_delivery(event: DeliverySimulationRequested) -> None:
        await handle_simulation_event(SimulationStream.DELIVERY, event.id, producer)

    bus = EventBus(redis, group=settings.simulator_group)
    bus.subscribe(OrderSimulationRequested, handle_order)
    bus.subscribe(DeliverySimulationRequested, handle_delivery)
    await bus.run_forever()
