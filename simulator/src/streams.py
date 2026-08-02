import asyncio
from typing import Any

from redis.asyncio import Redis
from shared.events.delivery import DeliverySimulationRequested
from shared.events.order import OrderSimulationRequested
from shared.redis.event_bus import EventBus
from shared.redis.publisher import StreamProducer
from shared.redis.scheduler import RedisScheduler

from src.schemas import SimulationStream
from src.settings import settings
from src.utils import run_step, start_simulation


async def start_streams(redis: Redis) -> None:
    producer: StreamProducer[Any] = StreamProducer(redis, source="simulator")
    scheduler = RedisScheduler(redis, key=settings.scheduler_key)

    async def handle_order(event: OrderSimulationRequested) -> None:
        await start_simulation(SimulationStream.ORDER, event.id, scheduler)

    async def handle_delivery(event: DeliverySimulationRequested) -> None:
        await start_simulation(SimulationStream.DELIVERY, event.id, scheduler)

    async def handle_timer(payload: dict[str, Any]) -> None:
        await run_step(payload, scheduler, producer)

    bus = EventBus(redis, group=settings.simulator_group)
    bus.subscribe(OrderSimulationRequested, handle_order)
    bus.subscribe(DeliverySimulationRequested, handle_delivery)

    # Either one stopping means the simulator is no longer doing its job, so
    # let the failure propagate and take the process with it.
    await asyncio.gather(bus.run_forever(), scheduler.run(handle_timer))
