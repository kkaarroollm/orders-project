import asyncio
import logging
from typing import Any

from shared.redis.publisher import StreamProducer

from src.schemas import SimulationStream
from src.strategies import SIMULATION_STRATEGY

SEMAPHORE = asyncio.Semaphore(10)


async def handle_simulation_event(
    stream: SimulationStream,
    data: dict[str, Any],
    producer: StreamProducer[Any],
) -> None:
    strategy = SIMULATION_STRATEGY.get(stream)
    if not strategy:
        logging.warning("No simulation strategy found for stream: %s", stream)
        return

    logging.info("Received simulation event for `%s` on `%s`", data.get("id"), stream.listen_stream)

    async def run() -> None:
        async with SEMAPHORE:
            await strategy.process(entity_id=data["id"], producer=producer, output_stream=stream.send_stream)

    asyncio.create_task(run())
