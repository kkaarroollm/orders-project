import asyncio
import logging

from redis.asyncio import Redis

from src.schemas import SimulationStream
from src.strategies import SIMULATION_STRATEGY

SEMAPHORE = asyncio.Semaphore(10)


async def handle_simulation_event(
    stream: SimulationStream,
    data: dict,
    redis: Redis,
) -> None:
    strategy = SIMULATION_STRATEGY.get(stream)
    if not strategy:
        logging.warning(f"🚫 No simulation strategy found for stream: {stream}")
        return

    logging.info(f"Received simulation event for `{data.get('id')}` on `{stream.listen_stream}`")

    async def run() -> None:
        async with SEMAPHORE:
            await strategy.process(entity_id=data["id"], redis_client=redis, output_stream=stream.send_stream)

    asyncio.create_task(run())
