import asyncio
import logging
from typing import Any

from shared.redis.publisher import StreamProducer

from src.schemas import SimulationStream
from src.strategies import SIMULATION_STRATEGY

SEMAPHORE = asyncio.Semaphore(10)


async def handle_simulation_event(
    stream: SimulationStream,
    entity_id: str,
    producer: StreamProducer[Any],
) -> None:
    strategy = SIMULATION_STRATEGY.get(stream)
    if not strategy:
        logging.warning("No simulation strategy found for stream: %s", stream)
        return

    logging.info("Received %s simulation event for `%s`", stream.name, entity_id)

    async def run() -> None:
        async with SEMAPHORE:
            await strategy.process(entity_id=entity_id, producer=producer)

    asyncio.create_task(run())
